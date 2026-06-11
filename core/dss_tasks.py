# core/dss_tasks.py
"""Celery tasks for the DSS modules (M3 deviation detection, M8 step SLA)."""
from celery_app import celery_app
from config import logger
# single source of truth for the active-tenant loop (was duplicated here)
from core.data_sources import active_tenant_ids as _active_tenant_ids
# Periodic beat tasks self-exclude: a still-running tick skips the next fire instead
# of overlapping it (wasted work + contending row locks that roll each other back).
from core.locking import single_run


@celery_app.task(time_limit=120, soft_time_limit=110)
@single_run("dss:evaluate_indicators", lease_ttl=130)
def evaluate_indicators_task():
    """M3: evaluate every active indicator against its corridor, per tenant."""
    try:
        from core.deviation_engine import indicator_evaluator
        totals = {"evaluated": 0, "skipped": 0, "breaching": 0,
                  "opened": 0, "resolved": 0, "chronic": 0}
        for tenant_id in _active_tenant_ids():
            s = indicator_evaluator.evaluate_tenant(tenant_id=tenant_id)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info(
            "Indicator evaluation: %d evaluated, %d breaching, %d opened, "
            "%d resolved, %d chronic",
            totals["evaluated"], totals["breaching"], totals["opened"],
            totals["resolved"], totals["chronic"],
        )
        return totals
    except Exception as e:
        logger.exception("Indicator evaluation failed")
        return {"error": str(e)}


@celery_app.task(time_limit=180, soft_time_limit=170)
@single_run("dss:correlate_situations", lease_ttl=190)
def correlate_situations_task(window_minutes: int = 30):
    """M4: correlate active deviations into situations, per tenant."""
    try:
        from core.situation_engine import situation_engine
        totals = {"clusters": 0, "created": 0, "updated": 0, "resolved": 0}
        for tenant_id in _active_tenant_ids():
            s = situation_engine.correlate_tenant(tenant_id=tenant_id, window_minutes=window_minutes)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info("Situation correlation: %d clusters, %d created, %d updated, %d resolved",
                    totals["clusters"], totals["created"], totals["updated"], totals["resolved"])
        return totals
    except Exception as e:
        logger.exception("Situation correlation failed")
        return {"error": str(e)}


@celery_app.task(time_limit=600, soft_time_limit=585)
@single_run("dss:predict_indicators", lease_ttl=610)
def predict_indicators_task(horizon_hours: int = 24):
    """M5: forecast each active indicator and raise predictive alerts on projected
    corridor breaches, per tenant. No-op where Prophet/data is unavailable."""
    try:
        from core.predictive_engine import predictive_engine
        totals = {"evaluated": 0, "skipped": 0, "raised": 0, "resolved": 0}
        for tenant_id in _active_tenant_ids():
            s = predictive_engine.evaluate_tenant(tenant_id=tenant_id, horizon_hours=horizon_hours)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info("Predictive: %d evaluated, %d raised, %d resolved, %d skipped",
                    totals["evaluated"], totals["raised"], totals["resolved"], totals["skipped"])
        return totals
    except Exception as e:
        logger.exception("Predictive task failed")
        return {"error": str(e)}


@celery_app.task(time_limit=120, soft_time_limit=110)
@single_run("dss:evaluate_decision_outcomes", lease_ttl=130)
def evaluate_decision_outcomes_task():
    """M10: auto-derive outcomes for accepted decisions whose process has finished."""
    try:
        from core.decision_engine import decision_engine
        total = 0
        for tenant_id in _active_tenant_ids():
            total += decision_engine.auto_evaluate(tenant_id=tenant_id).get("evaluated", 0)
        logger.info("Decision outcome evaluation: %d outcomes recorded", total)
        return {"evaluated": total}
    except Exception as e:
        logger.exception("Decision outcome evaluation failed")
        return {"error": str(e)}


@celery_app.task(time_limit=300, soft_time_limit=290)
@single_run("dss:monitor_forecast_drift", lease_ttl=310)
def monitor_forecast_drift_task(window_days: int = 7):
    """M5: score persisted forecasts against actuals, record MAE/RMSE/MAPE, and
    alert on model drift, per tenant."""
    try:
        from core.forecast_drift import drift_monitor
        totals = {"series": 0, "scored": 0, "drift_alerts": 0}
        for tenant_id in _active_tenant_ids():
            s = drift_monitor.compute_tenant(tenant_id=tenant_id, window_days=window_days)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info("Forecast drift: %d series, %d scored, %d drift alerts",
                    totals["series"], totals["scored"], totals["drift_alerts"])
        return totals
    except Exception as e:
        logger.exception("Forecast drift monitoring failed")
        return {"error": str(e)}


@celery_app.task(time_limit=120, soft_time_limit=110)
def verify_remediation_task(deviation_id: str, tenant_id: str = "default"):
    """OODA Act→Observe: re-measure after a remediation process completes.

    Scheduled (with a countdown) when an M8 process instance tied to a deviation
    finishes. READ-ONLY re-measure of the deviation's indicator, then records whether
    the breach cleared — 'confirmed' (back inside corridor → also resolve the
    deviation) or 'persisted' (still breaching → notify so an operator escalates).

    It deliberately does NOT run the full evaluate path: that would inflate
    periods/chronicle and could spuriously open a chronic incident, and its INSERT
    would race the periodic sweep on the partial-unique index. Here we only OBSERVE
    and do a targeted UPDATE by deviation id (never an INSERT).
    """
    from sqlalchemy import text
    from core.database import get_engine
    from core.deviation_engine import indicator_evaluator
    try:
        engine = get_engine()
        with engine.connect() as conn:
            dev = conn.execute(
                text("SELECT indicator_id, status FROM deviations "
                     "WHERE id = :id AND tenant_id = :tid"),
                {"id": deviation_id, "tid": tenant_id},
            ).mappings().first()
        if not dev:
            logger.info("remediation verify: deviation %s not found", deviation_id)
            return {"missing": True}

        # Read-only: is the indicator currently back inside its corridor?
        breach = indicator_evaluator.current_breach_status(dev["indicator_id"], tenant_id)
        cleared = breach == "clear"
        outcome = "confirmed" if cleared else "persisted"

        with engine.begin() as conn:
            if cleared:
                # Remediation worked → close the episode (idempotent: only if still open)
                # and stamp confirmation. Targeted by id — no INSERT, no race.
                conn.execute(
                    text("UPDATE deviations SET "
                         "status = CASE WHEN status <> 'resolved' THEN 'resolved' ELSE status END, "
                         "resolved_at = COALESCE(resolved_at, NOW()), last_seen = NOW(), "
                         "remediation_outcome = 'confirmed', remediation_verified_at = NOW() "
                         "WHERE id = :id AND tenant_id = :tid"),
                    {"id": deviation_id, "tid": tenant_id},
                )
            else:
                conn.execute(
                    text("UPDATE deviations SET remediation_outcome = 'persisted' "
                         "WHERE id = :id AND tenant_id = :tid"),
                    {"id": deviation_id, "tid": tenant_id},
                )

        from core.audit import log_audit
        log_audit("system", tenant_id, "verify_remediation", "deviation",
                  resource_id=str(deviation_id), changes={"outcome": outcome})
        try:
            from core.notifications import notify
            if cleared:
                notify(f"Устранение подтверждено: отклонение {deviation_id} вернулось в коридор",
                       "info", tenant_id=tenant_id)
            else:
                notify(f"Процесс завершён, но отклонение {deviation_id} всё ещё активно — "
                       f"меры не сработали, нужна эскалация", "warning", tenant_id=tenant_id)
        except Exception as e:
            logger.error("remediation verify notify failed: %s", e)

        logger.info("remediation verify: deviation %s → %s", deviation_id, outcome)
        return {"deviation_id": str(deviation_id), "outcome": outcome}
    except Exception as e:
        logger.exception("remediation verification failed")
        return {"error": str(e)}


@celery_app.task(time_limit=120, soft_time_limit=110)
@single_run("dss:check_process_step_sla", lease_ttl=130)
def check_process_step_sla_task():
    """M8: escalate process step assignments that are past their due_at."""
    try:
        from core.process_engine import process_engine
        total = 0
        for tenant_id in _active_tenant_ids():
            total += process_engine.escalate_overdue_steps(tenant_id=tenant_id)
        logger.info("Process step SLA check: %d steps escalated", total)
        return {"escalated": total}
    except Exception as e:
        logger.exception("Process step SLA check failed")
        return {"error": str(e)}
