# core/ml_tasks.py
import os

from sqlalchemy import text

from celery_app import celery_app
from config import logger
# single source of truth for the active-tenant loop (was duplicated here)
from core.data_sources import active_tenant_ids as _active_tenant_ids
from core.locking import single_run

# E: calibrated statistical anomaly detection knobs.
ANOMALY_DETECTION_ENABLED = os.environ.get("ANOMALY_DETECTION_ENABLED", "true").lower() in ("1", "true", "yes")
ANOMALY_TRAIN_WINDOW_MIN = int(os.environ.get("ANOMALY_TRAIN_WINDOW_MIN", str(24 * 60)))
ANOMALY_SCORE_WINDOW_MIN = int(os.environ.get("ANOMALY_SCORE_WINDOW_MIN", "15"))
ANOMALY_MAX_METRICS = int(os.environ.get("ANOMALY_MAX_METRICS", "200"))
ANOMALY_ALERT_TTL = int(os.environ.get("ANOMALY_ALERT_TTL", "3600"))  # per-metric alert cooldown


@celery_app.task(time_limit=60)
def evaluate_rules_task():
    try:
        from core.rule_engine import rule_engine
        from core.notifications import notify
        total_checked = 0
        total_fired = 0
        # Evaluate each tenant's rules against ONLY that tenant's metrics so rules
        # from one tenant never fire on another tenant's data.
        for tenant_id in _active_tenant_ids():
            results = rule_engine.evaluate_all_rules(tenant_id=tenant_id)
            fired = [r for r in results if r.fired]
            for r in fired:
                msg = f"Rule '{r.rule_name}': {r.metric_name} {r.operator} {r.threshold} (current: {r.current_value:.2f})"
                notify(msg, "warning", tenant_id=tenant_id)
            total_checked += len(results)
            total_fired += len(fired)
        logger.info("Rule evaluation: %d rules checked, %d fired", total_checked, total_fired)
        return {"checked": total_checked, "fired": total_fired}
    except Exception as e:
        logger.exception("Rule evaluation failed")
        return {"error": str(e)}


@celery_app.task(queue="ml", time_limit=600)
def run_ml_anomaly_check():
    try:
        from core.ml_anomaly import find_recent_ml_anomalies
        total = 0
        # Run detection per tenant so one tenant's metrics never feed another
        # tenant's anomaly models or results.
        for tenant_id in _active_tenant_ids():
            result = find_recent_ml_anomalies(time_filter="6h", tenant_id=tenant_id)
            total += result if isinstance(result, int) else len(result or [])
        logger.info(f"ML: found {total} anomalies")
        return total
    except Exception:
        logger.exception("ML task failed")
        return 0


@celery_app.task(queue="ml", time_limit=600)
def retrain_ml_models():
    try:
        from core.ml_anomaly import retrain_all_models
        for tenant_id in _active_tenant_ids():
            retrain_all_models(tenant_id=tenant_id)
        return {"status": "success"}
    except Exception as e:
        logger.exception("Retrain ML failed")
        return {"status": "error", "message": str(e)}


def _detect_metric(conn, tenant_id: str, metric_name: str) -> list:
    """Train robust stats on history, score the recent window, persist NEW anomalies.
    Runs on the DEFAULT worker (no TF/torch). Returns the anomalies inserted this run."""
    from core.anomaly_detect import detect_anomalies

    rows = conn.execute(
        text("SELECT timestamp, AVG(value) AS v FROM canonical_metrics "
             "WHERE tenant_id = :tid AND metric_name = :m "
             "AND timestamp >= NOW() - make_interval(mins => :win) "
             "GROUP BY timestamp ORDER BY timestamp"),
        {"tid": tenant_id, "m": metric_name, "win": ANOMALY_TRAIN_WINDOW_MIN},
    ).all()
    if not rows:
        return []
    # Split: the recent SCORE window is judged against the older TRAIN baseline, so the
    # detector is never fit on the points it scores (calibration discipline).
    cutoff = conn.execute(
        text("SELECT NOW() - make_interval(mins => :s)"), {"s": ANOMALY_SCORE_WINDOW_MIN}
    ).scalar()
    train = [float(r.v) for r in rows if r.timestamp < cutoff]
    score = [(r.timestamp, float(r.v)) for r in rows if r.timestamp >= cutoff]
    found = detect_anomalies(train, score)
    if not found:
        return []
    # Skip timestamps already recorded this method, so reruns don't duplicate.
    seen = {r[0] for r in conn.execute(
        text("SELECT timestamp FROM ml_anomalies WHERE tenant_id = :tid AND metric_name = :m "
             "AND method = 'robust_zscore' AND timestamp >= NOW() - make_interval(mins => :s)"),
        {"tid": tenant_id, "m": metric_name, "s": ANOMALY_SCORE_WINDOW_MIN},
    ).all()}
    fresh = [a for a in found if a["timestamp"] not in seen]
    for a in fresh:
        conn.execute(
            text("INSERT INTO ml_anomalies (ml_config_id, metric_name, dimensions, timestamp, "
                 "value, predicted, residual, confidence, method, tenant_id) "
                 "VALUES (NULL, :m, '{}'::jsonb, :ts, :val, :pred, :res, :conf, 'robust_zscore', :tid)"),
            {"m": metric_name, "ts": a["timestamp"], "val": a["value"], "pred": a["predicted"],
             "res": a["value"] - a["predicted"], "conf": a["confidence"], "tid": tenant_id},
        )
    return fresh


def _alert_anomalies(tenant_id: str, metric_name: str, anomalies: list) -> None:
    """One concise, rate-limited alert per metric per run — surfaced on the Alerts stream.
    A Redis cooldown key suppresses repeats for an ongoing anomaly."""
    if not anomalies:
        return
    try:
        from config import get_redis
        rkey = f"anomaly_alert:{tenant_id}:{metric_name}"
        if get_redis().get(rkey):
            return
        get_redis().set(rkey, "1", ex=ANOMALY_ALERT_TTL)
    except Exception:
        pass  # no Redis → alert anyway (best effort)
    worst = max(anomalies, key=lambda a: abs(a["zscore"]))
    try:
        from core.notifications import notify
        notify(f"📈 Аномалия в метрике «{metric_name}»: {len(anomalies)} точек вне нормы "
               f"(худшая z={worst['zscore']:.1f}, значение {worst['value']:.2f} при норме "
               f"≈{worst['predicted']:.2f}).", "warning", tenant_id=tenant_id)
    except Exception as e:
        logger.error("anomaly notify failed: %s", e)


@celery_app.task(time_limit=300, soft_time_limit=290)
@single_run("ml:detect_metric_anomalies", lease_ttl=320)
def detect_metric_anomalies_task():
    """E: calibrated, dependency-light anomaly detection over every live metric, per
    tenant. Modified z-score (median/MAD), trained on history excluding the scored window.
    Persists to ml_anomalies (method='robust_zscore') and raises a rate-limited alert.
    Opt-out via ANOMALY_DETECTION_ENABLED=false."""
    if not ANOMALY_DETECTION_ENABLED:
        return {"disabled": True}
    from core.database import get_engine
    try:
        total = 0
        for tenant_id in _active_tenant_ids():
            engine = get_engine()
            with engine.connect() as conn:
                metrics = conn.execute(
                    text("SELECT DISTINCT metric_name FROM canonical_metrics "
                         "WHERE tenant_id = :tid AND timestamp >= NOW() - make_interval(mins => :s) "
                         "ORDER BY metric_name LIMIT :lim"),
                    {"tid": tenant_id, "s": ANOMALY_SCORE_WINDOW_MIN, "lim": ANOMALY_MAX_METRICS},
                ).scalars().all()
            for m in metrics:
                with engine.begin() as conn:
                    fresh = _detect_metric(conn, tenant_id, m)
                if fresh:
                    _alert_anomalies(tenant_id, m, fresh)
                    total += len(fresh)
        logger.info("Anomaly detection: %d new anomalies (robust z-score)", total)
        return {"anomalies": total}
    except Exception as e:
        logger.exception("Anomaly detection failed")
        return {"error": str(e)}
