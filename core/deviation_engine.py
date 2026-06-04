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
from typing import Optional, Dict
from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets

# Window over which an indicator's current value is averaged (minutes).
WINDOW_MINUTES = 5


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


def fingerprint_for(indicator_id) -> str:
    # MVP: one fingerprint per indicator (no per-dimension split yet).
    return f"ind:{indicator_id}"


class IndicatorEvaluator:
    def evaluate_tenant(self, tenant_id: str = "default", window_minutes: int = WINDOW_MINUTES) -> dict:
        engine = get_engine()
        summary = {"evaluated": 0, "skipped": 0, "breaching": 0,
                   "opened": 0, "resolved": 0, "chronic": 0}
        with engine.connect() as conn:
            indicators = conn.execute(
                text(
                    "SELECT id, name, target_low, target_high, direction, chronicle_threshold "
                    "FROM indicators WHERE tenant_id = :tid AND is_active = true"
                ),
                {"tid": tenant_id},
            ).mappings().all()

        for ind in indicators:
            try:
                self._evaluate_one(ind, tenant_id, window_minutes, summary)
            except Exception as e:
                logger.error("indicator eval failed for %s: %s", ind["name"], mask_secrets(str(e)))
        return summary

    # -- value computation -------------------------------------------------
    def _indicator_value(self, indicator_id, tenant_id: str, window_minutes: int) -> Optional[float]:
        """Weighted average of factor values; factor value = mean of its metrics'
        recent averages. Returns None when nothing recent is available."""
        engine = get_engine()
        with engine.connect() as conn:
            factors = conn.execute(
                text("SELECT id, weight FROM factors WHERE indicator_id = :iid"),
                {"iid": indicator_id},
            ).mappings().all()
            if not factors:
                return None

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
                return None

            rows = conn.execute(
                text(
                    "SELECT metric_name, AVG(value) AS v FROM canonical_metrics "
                    "WHERE tenant_id = :tid AND metric_name = ANY(:names) "
                    "AND timestamp >= NOW() - make_interval(mins => :win) "
                    "GROUP BY metric_name"
                ),
                {"tid": tenant_id, "names": list(all_names), "win": window_minutes},
            ).mappings().all()

        latest = {r["metric_name"]: float(r["v"]) for r in rows}
        num = 0.0
        den = 0.0
        for weight, names in factor_metrics.values():
            vals = [latest[n] for n in names if n in latest]
            if not vals:
                continue
            factor_value = sum(vals) / len(vals)
            num += factor_value * weight
            den += weight
        if den == 0:
            return None
        return num / den

    # -- per-indicator evaluation -----------------------------------------
    def _evaluate_one(self, ind, tenant_id: str, window_minutes: int, summary: dict):
        value = self._indicator_value(ind["id"], tenant_id, window_minutes)
        if value is None:
            summary["skipped"] += 1
            return
        summary["evaluated"] += 1

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
                        "periods = :p, last_seen = NOW() WHERE id = :id"
                    ),
                    {"v": value, "dir": breach_dir,
                     "sev": "critical" if periods >= threshold else severity,
                     "p": periods, "id": existing["id"]},
                )
            else:
                periods = 1
                newly_opened = True
                dev_id = conn.execute(
                    text(
                        "INSERT INTO deviations (tenant_id, indicator_id, direction, value, "
                        "target_low, target_high, severity, status, periods, fingerprint) "
                        "VALUES (:tid, :iid, :dir, :v, :low, :high, :sev, 'open', 1, :fp) RETURNING id"
                    ),
                    {"tid": tenant_id, "iid": ind["id"], "dir": breach_dir, "v": value,
                     "low": low, "high": high,
                     "sev": "critical" if periods >= threshold else severity, "fp": fp},
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
                     "VALUES (:msg, :metric, 'all', :val, 'critical', 'new', NOW(), :desc, :tid) "
                     "RETURNING id"),
                {"msg": msg, "metric": ind["name"], "val": str(round(value, 2)),
                 "desc": "Авто-инцидент из DSS (хроническое отклонение показателя)", "tid": tenant_id},
            ).scalar()
            conn.execute(
                text("UPDATE deviations SET incident_id = :inc WHERE id = :id"),
                {"inc": inc_id, "id": dev_id},
            )
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
            notify(msg, priority)
        except Exception as e:
            logger.error("deviation notify failed: %s", mask_secrets(str(e)))


indicator_evaluator = IndicatorEvaluator()
