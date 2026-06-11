# core/deviation_engine.py
"""DSS M3 — Deviation Detection & Chronicle.

Evaluates each active indicator (M2) against its target corridor, two-sided, and
maintains:
  * deviations — one row per breach episode (open → acknowledged → resolved), with
    `periods` = consecutive breaching evaluation cycles (the episode's "chronicle");
  * chronicles — the longitudinal per-indicator summary (episodes / total / max streak).

The corridor classification is pure (classify_breach / breach_severity) so it is
unit-tested without a database. The evaluation loop is meant to run from a Celery
beat task (see core/dss_tasks.py).
"""
import os
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets

# Window over which an indicator's current value is averaged (minutes). Configurable
# via EVAL_WINDOW_MIN — a shorter window reacts to brief spikes faster (the demo uses
# 1); the default 5 smooths noise for production.
WINDOW_MINUTES = int(os.environ.get("EVAL_WINDOW_MIN", "5"))

# Dynamic-corridor ('baseline') params: corridor = weighted mean ± K·std over this
# historical window (minutes). Defaults: 7 days, 3σ.
BASELINE_WINDOW_MIN = int(os.environ.get("BASELINE_WINDOW_MIN", str(7 * 24 * 60)))
BASELINE_K = float(os.environ.get("BASELINE_K", "3"))


def classify_breach(
    value: float,
    low: Optional[float],
    high: Optional[float],
    direction: str,
) -> Optional[str]:
    """Return 'below' / 'above' if `value` is outside the corridor on a watched
    side, else None. `direction` (both|below|above) selects which side counts."""
    below = low is not None and value < low
    above = high is not None and value > high
    if direction in ("both", "below") and below:
        return "below"
    if direction in ("both", "above") and above:
        return "above"
    return None


def breach_severity(
    value: float,
    low: Optional[float],
    high: Optional[float],
    breach_dir: str,
) -> str:
    """'critical' if the breach margin exceeds half a reference scale, else 'warning'.

    Reference scale = corridor width when both bounds exist, otherwise the magnitude
    of the breached bound. Chronicle escalation can still bump 'warning' → 'critical'
    in the evaluation loop when a breach persists."""
    if breach_dir == "below" and low is not None:
        margin = low - value
        ref = (high - low) if (high is not None and high > low) else abs(low)
    elif breach_dir == "above" and high is not None:
        margin = value - high
        ref = (high - low) if (low is not None and high > low) else abs(high)
    else:
        return "warning"
    if ref and ref > 0 and margin > 0.5 * ref:
        return "critical"
    return "warning"


def breach_severity_score(
    value: float,
    low: Optional[float],
    high: Optional[float],
    breach_dir: str,
    periods: int = 1,
    chronicle_threshold: int = 3,
) -> float:
    """Continuous, rankable severity: breach margin normalised by the reference scale
    (0 at the boundary, 1 when the margin equals the scale), boosted by persistence so a
    chronic breach ranks above a fresh one of the same depth. Pure → unit-tested."""
    if breach_dir == "below" and low is not None:
        margin = low - value
        ref = (high - low) if (high is not None and high > low) else abs(low)
    elif breach_dir == "above" and high is not None:
        margin = value - high
        ref = (high - low) if (low is not None and high > low) else abs(high)
    else:
        return 0.0
    if not ref or ref <= 0 or margin <= 0:
        return 0.0
    depth = margin / ref
    persistence = 1.0 + min(periods, chronicle_threshold) / max(chronicle_threshold, 1)
    return round(depth * persistence, 4)


def fingerprint_for(indicator_id) -> str:
    # MVP: one fingerprint per indicator (no per-dimension split yet).
    return f"ind:{indicator_id}"


class IndicatorEvaluator:
    def evaluate_tenant(self, tenant_id: str = "default", window_minutes: int = WINDOW_MINUTES) -> dict:
        engine = get_engine()
        summary = {"evaluated": 0, "skipped": 0, "no_data": 0, "breaching": 0,
                   "opened": 0, "resolved": 0, "chronic": 0}
        with engine.connect() as conn:
            indicators = conn.execute(
                text(
                    "SELECT id, name, target_low, target_high, direction, chronicle_threshold, "
                    "corridor_type FROM indicators WHERE tenant_id = :tid AND is_active = true"
                ),
                {"tid": tenant_id},
            ).mappings().all()

        for ind in indicators:
            try:
                self._evaluate_one(ind, tenant_id, window_minutes, summary)
            except Exception as e:
                logger.error("indicator eval failed for %s: %s", ind["name"], mask_secrets(str(e)))
        return summary

    def reevaluate_indicator(self, indicator_id, tenant_id: str = "default",
                             window_minutes: int = WINDOW_MINUTES) -> dict:
        """Force a fresh evaluation of a SINGLE active indicator (same path as the
        periodic sweep, scoped to one id). Used by the OODA Act→Observe re-check so a
        deviation's status reflects the current measurement, not the last beat tick."""
        engine = get_engine()
        summary = {"evaluated": 0, "skipped": 0, "no_data": 0, "breaching": 0,
                   "opened": 0, "resolved": 0, "chronic": 0}
        with engine.connect() as conn:
            ind = conn.execute(
                text(
                    "SELECT id, name, target_low, target_high, direction, chronicle_threshold, "
                    "corridor_type FROM indicators "
                    "WHERE id = :iid AND tenant_id = :tid AND is_active = true"
                ),
                {"iid": indicator_id, "tid": tenant_id},
            ).mappings().first()
        if ind:
            try:
                self._evaluate_one(ind, tenant_id, window_minutes, summary)
            except Exception as e:
                logger.error("indicator re-eval failed for %s: %s", ind["name"], mask_secrets(str(e)))
        return summary

    # -- value computation -------------------------------------------------
    def _gather_factor_metrics(self, conn, indicator_id):
        """Return (factor_metrics: {fid: (weight, [names])}, all_names: set) or
        (None, None) when the indicator has no factors/metrics configured."""
        factors = conn.execute(
            text("SELECT id, weight FROM factors WHERE indicator_id = :iid"),
            {"iid": indicator_id},
        ).mappings().all()
        if not factors:
            return None, None
        factor_metrics: Dict = {}
        all_names: set = set()
        for f in factors:
            names = conn.execute(
                text("SELECT metric_name FROM factor_metrics WHERE factor_id = :fid"),
                {"fid": f["id"]},
            ).scalars().all()
            factor_metrics[f["id"]] = (float(f["weight"]), list(names))
            all_names.update(names)
        if not all_names:
            return None, None
        return factor_metrics, all_names

    @staticmethod
    def _weighted(factor_metrics, per_metric) -> Optional[float]:
        """Weighted mean of factor values; factor value = mean of its metrics' values
        from `per_metric`. None when no factor has any available metric."""
        num = den = 0.0
        for weight, names in factor_metrics.values():
            vals = [per_metric[n] for n in names if n in per_metric]
            if not vals:
                continue
            num += (sum(vals) / len(vals)) * weight
            den += weight
        return (num / den) if den else None

    def _value_status(self, indicator_id, tenant_id: str, window_minutes: int):
        """Return ('unconfigured'|'no_data'|'ok', value_or_None). 'no_data' means the
        indicator HAS metrics configured but none reported in the window — a signal
        (dead source), not a healthy skip."""
        engine = get_engine()
        with engine.connect() as conn:
            factor_metrics, all_names = self._gather_factor_metrics(conn, indicator_id)
            if not factor_metrics:
                return "unconfigured", None
            rows = conn.execute(
                text(
                    "SELECT metric_name, AVG(value) AS v FROM canonical_metrics "
                    "WHERE tenant_id = :tid AND metric_name = ANY(:names) "
                    "AND timestamp >= NOW() - make_interval(mins => :win) "
                    "GROUP BY metric_name"
                ),
                {"tid": tenant_id, "names": list(all_names), "win": window_minutes},
            ).mappings().all()
        per_metric = {r["metric_name"]: float(r["v"]) for r in rows}
        if not per_metric:
            return "no_data", None
        value = self._weighted(factor_metrics, per_metric)
        if value is None:
            return "no_data", None
        return "ok", value

    def _indicator_value(self, indicator_id, tenant_id: str, window_minutes: int) -> Optional[float]:
        """Back-compat scalar value (used by scenario_engine); None if unavailable."""
        _, value = self._value_status(indicator_id, tenant_id, window_minutes)
        return value

    def _baseline_corridor(self, indicator_id, tenant_id: str):
        """Dynamic corridor for corridor_type='baseline': weighted mean ± K·std of the
        indicator's metrics over BASELINE_WINDOW_MIN. Returns (low, high) or (None, None)
        if there isn't enough history."""
        engine = get_engine()
        with engine.connect() as conn:
            factor_metrics, all_names = self._gather_factor_metrics(conn, indicator_id)
            if not factor_metrics:
                return None, None
            rows = conn.execute(
                text(
                    "SELECT metric_name, AVG(value) AS mean, "
                    "COALESCE(STDDEV_SAMP(value), 0) AS sd FROM canonical_metrics "
                    "WHERE tenant_id = :tid AND metric_name = ANY(:names) "
                    "AND timestamp >= NOW() - make_interval(mins => :win) GROUP BY metric_name"
                ),
                {"tid": tenant_id, "names": list(all_names), "win": BASELINE_WINDOW_MIN},
            ).mappings().all()
        means = {r["metric_name"]: float(r["mean"]) for r in rows}
        stds = {r["metric_name"]: float(r["sd"]) for r in rows}
        wmean = self._weighted(factor_metrics, means)
        wstd = self._weighted(factor_metrics, stds)
        if wmean is None or wstd is None:
            return None, None
        return wmean - BASELINE_K * wstd, wmean + BASELINE_K * wstd

    # -- per-indicator evaluation -----------------------------------------
    def _evaluate_one(self, ind, tenant_id: str, window_minutes: int, summary: dict):
        status, value = self._value_status(ind["id"], tenant_id, window_minutes)
        if status == "unconfigured":
            summary["skipped"] += 1
            return
        if status == "no_data":
            # configured but the source went dark — a SIGNAL, not a healthy skip
            summary["no_data"] += 1
            self._signal_no_data(ind, tenant_id, window_minutes)
            return
        summary["evaluated"] += 1
        self._clear_no_data_flag(tenant_id, ind["id"])  # data is back

        # Corridor bounds: static (target_low/high) or a dynamic 'baseline' band.
        if ind["corridor_type"] == "baseline":
            low, high = self._baseline_corridor(ind["id"], tenant_id)
        else:
            low = float(ind["target_low"]) if ind["target_low"] is not None else None
            high = float(ind["target_high"]) if ind["target_high"] is not None else None
        breach_dir = classify_breach(value, low, high, ind["direction"])
        threshold = int(ind["chronicle_threshold"])
        fp = fingerprint_for(ind["id"])

        engine = get_engine()
        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT id, periods FROM deviations "
                    "WHERE tenant_id = :tid AND fingerprint = :fp AND status <> 'resolved' "
                    "FOR UPDATE"
                ),
                {"tid": tenant_id, "fp": fp},
            ).mappings().first()

            if breach_dir is None:
                # Back inside the corridor — close any active episode.
                if existing:
                    conn.execute(
                        text(
                            "UPDATE deviations SET status = 'resolved', resolved_at = NOW(), "
                            "last_seen = NOW() WHERE id = :id"
                        ),
                        {"id": existing["id"]},
                    )
                    summary["resolved"] += 1
                return

            summary["breaching"] += 1
            severity = breach_severity(value, low, high, breach_dir)
            dev_id = None

            if existing:
                periods = existing["periods"] + 1
                newly_opened = False
                dev_id = existing["id"]
                conn.execute(
                    text(
                        "UPDATE deviations SET value = :v, direction = :dir, severity = :sev, "
                        "severity_score = :score, periods = :p, last_seen = NOW() WHERE id = :id"
                    ),
                    {"v": value, "dir": breach_dir,
                     "sev": "critical" if periods >= threshold else severity,
                     "score": breach_severity_score(value, low, high, breach_dir, periods, threshold),
                     "p": periods, "id": existing["id"]},
                )
            else:
                periods = 1
                newly_opened = True
                dev_id = conn.execute(
                    text(
                        "INSERT INTO deviations (tenant_id, indicator_id, direction, value, "
                        "target_low, target_high, severity, severity_score, status, periods, fingerprint) "
                        "VALUES (:tid, :iid, :dir, :v, :low, :high, :sev, :score, 'open', 1, :fp) RETURNING id"
                    ),
                    {"tid": tenant_id, "iid": ind["id"], "dir": breach_dir, "v": value,
                     "low": low, "high": high,
                     "sev": "critical" if periods >= threshold else severity,
                     "score": breach_severity_score(value, low, high, breach_dir, periods, threshold),
                     "fp": fp},
                ).scalar()
                summary["opened"] += 1

            # Crossing the chronicle threshold this cycle = a persistent deviation.
            newly_chronic = periods == threshold
            if newly_chronic:
                summary["chronic"] += 1

            # Longitudinal chronicle aggregate.
            conn.execute(
                text(
                    "INSERT INTO chronicles (tenant_id, indicator_id, fingerprint, episodes, "
                    "total_periods, max_periods, first_seen, last_seen) "
                    "VALUES (:tid, :iid, :fp, :ep, 1, :p, NOW(), NOW()) "
                    "ON CONFLICT (tenant_id, fingerprint) DO UPDATE SET "
                    "episodes = chronicles.episodes + :ep, "
                    "total_periods = chronicles.total_periods + 1, "
                    "max_periods = GREATEST(chronicles.max_periods, :p), "
                    "last_seen = NOW()"
                ),
                {"tid": tenant_id, "iid": ind["id"], "fp": fp,
                 "ep": 1 if newly_opened else 0, "p": periods},
            )

            if newly_opened or newly_chronic:
                self._notify(conn, ind, tenant_id, value, breach_dir, periods, threshold)

        # On a chronic (persistent) deviation, best-effort after the txn commits:
        if newly_chronic and dev_id is not None:
            # Consolidation: open a classic Incident (the single ITSM ticket tail) —
            # one per deviation, deduped via deviations.incident_id.
            try:
                summary["incidents"] = summary.get("incidents", 0) + (
                    1 if self._ensure_incident(dev_id, ind, tenant_id, value, breach_dir, periods) else 0)
            except Exception as e:
                logger.error("auto-incident on chronic failed: %s", mask_secrets(str(e)))
            # M3 → M7: auto-generate Next-Best-Action recommendations.
            try:
                from core.recommendation_engine import recommendation_engine
                recommendation_engine.generate(tenant_id, deviation_id=dev_id)
                summary["recommended"] = summary.get("recommended", 0) + 1
            except Exception as e:
                logger.error("auto-recommend on chronic failed: %s", mask_secrets(str(e)))

    def _ensure_incident(self, dev_id, ind, tenant_id, value, breach_dir, periods) -> bool:
        """Create a classic incident for a chronic deviation, deduped via
        deviations.incident_id. Returns True if a new incident was created."""
        engine = get_engine()
        now = datetime.now(timezone.utc)
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT incident_id FROM deviations WHERE id = :id FOR UPDATE"),
                {"id": dev_id},
            ).scalar()
            if existing:
                return False
            msg = (f"Показатель '{ind['name']}': значение {value:.2f} вне коридора "
                   f"({breach_dir}), хроника {periods} периодов")
            inc_id = conn.execute(
                text("INSERT INTO incidents (alert_message, metric, region, value, priority, "
                     "status, detected_at, description, tenant_id) "
                     "VALUES (:msg, :metric, 'all', :val, 'critical', 'new', :now, :desc, :tid) "
                     "RETURNING id"),
                {"msg": msg, "metric": ind["name"], "val": str(round(value, 2)), "now": now,
                 "desc": "Авто-инцидент из DSS (хроническое отклонение показателя)", "tid": tenant_id},
            ).scalar()
            conn.execute(
                text("UPDATE deviations SET incident_id = :inc WHERE id = :id"),
                {"inc": inc_id, "id": dev_id},
            )
            # Attach the tenant's default escalation chain so auto-escalation
            # (check_auto_escalation skips incidents with no chain) can act on it.
            chain = conn.execute(
                text("SELECT id FROM escalation_chains WHERE tenant_id = :tid "
                     "AND is_active = true ORDER BY created_at LIMIT 1"),
                {"tid": tenant_id},
            ).scalar()
            if chain:
                conn.execute(
                    text("UPDATE incidents SET escalation_chain_id = :cid WHERE id = :id"),
                    {"cid": chain, "id": inc_id},
                )
        # Apply the SLA policy (response/resolution deadlines) like create_incident does,
        # outside the txn above — otherwise the incident shows "SLA: N/A".
        try:
            from core.sla_service import apply_sla_to_incident
            apply_sla_to_incident(inc_id, tenant_id, "critical", now)
        except Exception as e:
            logger.error("apply SLA to auto-incident failed: %s", mask_secrets(str(e)))
        return True

    def _notify(self, conn, ind, tenant_id, value, breach_dir, periods, threshold):
        subs = conn.execute(
            text(
                "SELECT subscriber_role, subscriber_user FROM indicator_subscriptions "
                "WHERE indicator_id = :iid AND tenant_id = :tid"
            ),
            {"iid": ind["id"], "tid": tenant_id},
        ).mappings().all()
        watchers = ", ".join(
            s["subscriber_user"] or s["subscriber_role"] for s in subs
        ) or "—"
        priority = "critical" if periods >= threshold else "warning"
        chronic = " ХРОНИКА" if periods >= threshold else ""
        msg = (
            f"Показатель '{ind['name']}': значение {value:.2f} вышло за коридор "
            f"({breach_dir}), период {periods}/{threshold}{chronic}. Подписчики: {watchers}"
        )
        try:
            from core.notifications import notify
            notify(msg, priority, event_type="alert")
        except Exception as e:
            logger.error("deviation notify failed: %s", mask_secrets(str(e)))

    def _signal_no_data(self, ind, tenant_id, window_minutes):
        """Emit a deduped 'no data' signal (≤ once/hour per indicator) — a dead source
        must not read as a healthy/static state."""
        try:
            from config import get_redis
            r = get_redis()
            if r.get(f"nodata:{tenant_id}:{ind['id']}"):
                return  # already signalled this gap
            r.set(f"nodata:{tenant_id}:{ind['id']}", "1", ex=3600)
        except Exception:
            pass  # no Redis → still notify (best effort; may repeat)
        try:
            from core.notifications import notify
            notify(
                f"Показатель '{ind['name']}': нет данных за {window_minutes} мин — источник молчит?",
                "warning", event_type="system",
            )
        except Exception as e:
            logger.error("no-data notify failed: %s", mask_secrets(str(e)))

    def _clear_no_data_flag(self, tenant_id, indicator_id):
        try:
            from config import get_redis
            get_redis().delete(f"nodata:{tenant_id}:{indicator_id}")
        except Exception:
            pass


indicator_evaluator = IndicatorEvaluator()
