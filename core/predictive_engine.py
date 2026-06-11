# core/predictive_engine.py
"""DSS M5 — Forecasting & Predictive Alerts (Project / L3 Projection).

Projects each indicator forward and, if the forecast or its confidence band is
predicted to leave the target corridor within the horizon, raises a predictive alert
("act early"). The corridor projection (project_breach) is pure and unit-tested.
Forecast generation is reached through a seam (forecast_and_evaluate → Prophet) so
the lifecycle is fully testable by feeding synthetic points to evaluate_indicator,
without requiring ML libraries.
"""
import json
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets


def project_breach(
    points: List[Dict[str, Any]],
    low: Optional[float],
    high: Optional[float],
    direction: str,
) -> Optional[Dict[str, Any]]:
    """First forecast point predicted to leave the corridor, else None.

    `points`: list of {'ts', 'yhat', 'yhat_low', 'yhat_high'} sorted ascending in time.
    'above' uses the upper band edge (yhat_high) as the early-warning trigger; 'below'
    uses the lower edge (yhat_low). confidence='high' when the central yhat itself
    breaches, 'medium' when only the band does. Falls back to yhat if a band is absent."""
    for p in points:
        yhat = p["yhat"]
        upper = p.get("yhat_high")
        upper = upper if upper is not None else yhat
        lower = p.get("yhat_low")
        lower = lower if lower is not None else yhat

        if direction in ("both", "above") and high is not None and upper > high:
            return {"ts": p["ts"], "projected_value": yhat, "direction": "above",
                    "confidence": "high" if yhat > high else "medium"}
        if direction in ("both", "below") and low is not None and lower < low:
            return {"ts": p["ts"], "projected_value": yhat, "direction": "below",
                    "confidence": "high" if yhat < low else "medium"}
    return None


class PredictiveEngine:
    def evaluate_tenant(self, tenant_id: str = "default", horizon_hours: int = 24) -> dict:
        engine = get_engine()
        summary = {"evaluated": 0, "skipped": 0, "raised": 0, "resolved": 0}
        with engine.connect() as conn:
            ids = conn.execute(
                text("SELECT id FROM indicators WHERE tenant_id = :tid AND is_active = true "
                     "AND (target_low IS NOT NULL OR target_high IS NOT NULL)"),
                {"tid": tenant_id},
            ).scalars().all()
        for indicator_id in ids:
            try:
                res = self.forecast_and_evaluate(indicator_id, tenant_id, horizon_hours)
                status = res.get("status")
                if status == "evaluated":
                    summary["evaluated"] += 1
                    summary["raised"] += res.get("raised", 0)
                    summary["resolved"] += res.get("resolved", 0)
                else:
                    summary["skipped"] += 1
            except Exception as e:
                logger.error("predictive eval failed for %s: %s", indicator_id, mask_secrets(str(e)))
                summary["skipped"] += 1
        return summary

    def forecast_and_evaluate(self, indicator_id, tenant_id: str, horizon_hours: int = 24) -> dict:
        """Produce a Prophet forecast for the indicator's (single) metric and evaluate it.
        Returns {'status': ...}. Gracefully skips multi-metric indicators and missing ML."""
        engine = get_engine()
        with engine.connect() as conn:
            ind = conn.execute(
                text("SELECT target_low, target_high, direction FROM indicators "
                     "WHERE id = :id AND tenant_id = :tid AND is_active = true"),
                {"id": indicator_id, "tid": tenant_id},
            ).mappings().first()
            if not ind:
                return {"status": "not_found"}
            metrics = conn.execute(
                text("SELECT DISTINCT fm.metric_name FROM factors f "
                     "JOIN factor_metrics fm ON fm.factor_id = f.id WHERE f.indicator_id = :id"),
                {"id": indicator_id},
            ).scalars().all()

        if len(metrics) != 1:
            # MVP forecasts single-source indicators; multi-metric aggregation is future.
            return {"status": "skipped_multimetric", "metrics": len(metrics)}
        metric = metrics[0]

        try:
            from api.routes.forecasts import _generate_forecast
            fps = _generate_forecast(metric, {}, horizon_hours, tenant_id)
        except ImportError:
            logger.info("M5: Prophet unavailable — skipping predictive eval")
            return {"status": "no_prophet"}
        except ValueError:
            return {"status": "insufficient_data"}

        points = [{"ts": p.timestamp, "yhat": p.value, "yhat_low": p.lower, "yhat_high": p.upper}
                  for p in fps]
        return self.evaluate_indicator(
            indicator_id, tenant_id, points, horizon_hours, metric,
            low=float(ind["target_low"]) if ind["target_low"] is not None else None,
            high=float(ind["target_high"]) if ind["target_high"] is not None else None,
            direction=ind["direction"],
        )

    def evaluate_indicator(self, indicator_id, tenant_id: str, points: List[Dict[str, Any]],
                           horizon_hours: int, metric_name: str, *,
                           low: Optional[float] = None, high: Optional[float] = None,
                           direction: Optional[str] = None, model_version: Optional[str] = None) -> dict:
        """Store the forecast snapshot, project a breach, and drive the predictive-alert
        lifecycle. Corridor/direction default to the indicator's own when not given."""
        engine = get_engine()
        if low is None and high is None and direction is None:
            with engine.connect() as conn:
                ind = conn.execute(
                    text("SELECT target_low, target_high, direction FROM indicators "
                         "WHERE id = :id AND tenant_id = :tid"),
                    {"id": indicator_id, "tid": tenant_id},
                ).mappings().first()
            if not ind:
                return {"status": "not_found"}
            low = float(ind["target_low"]) if ind["target_low"] is not None else None
            high = float(ind["target_high"]) if ind["target_high"] is not None else None
            direction = ind["direction"]

        projection = project_breach(points, low, high, direction or "both")
        fp = f"pred:{indicator_id}"
        raised = 0
        resolved = 0

        with engine.begin() as conn:
            # Snapshot for the cockpit chart.
            conn.execute(
                text("INSERT INTO forecasts (tenant_id, indicator_id, metric_name, horizon_hours, "
                     "model_version, points) VALUES (:tid, :iid, :m, :h, :mv, CAST(:pts AS jsonb))"),
                {"tid": tenant_id, "iid": indicator_id, "m": metric_name, "h": horizon_hours,
                 "mv": model_version, "pts": _points_json(points)},
            )

            existing = conn.execute(
                text("SELECT id FROM predictive_alerts WHERE tenant_id = :tid AND fingerprint = :fp "
                     "AND status <> 'resolved' FOR UPDATE"),
                {"tid": tenant_id, "fp": fp},
            ).mappings().first()

            if projection:
                if existing:
                    conn.execute(
                        text("UPDATE predictive_alerts SET direction = :dir, projected_value = :pv, "
                             "breach_eta = :eta, confidence = :conf, horizon_hours = :h, "
                             "target_low = :low, target_high = :high, last_seen = NOW() WHERE id = :id"),
                        {"dir": projection["direction"], "pv": projection["projected_value"],
                         "eta": projection["ts"], "conf": projection["confidence"],
                         "h": horizon_hours, "low": low, "high": high, "id": existing["id"]},
                    )
                else:
                    conn.execute(
                        text("INSERT INTO predictive_alerts (tenant_id, indicator_id, direction, "
                             "projected_value, target_low, target_high, breach_eta, horizon_hours, "
                             "confidence, status, fingerprint) VALUES (:tid, :iid, :dir, :pv, :low, "
                             ":high, :eta, :h, :conf, 'open', :fp)"),
                        {"tid": tenant_id, "iid": indicator_id, "dir": projection["direction"],
                         "pv": projection["projected_value"], "low": low, "high": high,
                         "eta": projection["ts"], "h": horizon_hours,
                         "conf": projection["confidence"], "fp": fp},
                    )
                    raised = 1
                    self._notify(conn, indicator_id, tenant_id, projection)
            elif existing:
                conn.execute(
                    text("UPDATE predictive_alerts SET status = 'resolved', resolved_at = NOW(), "
                         "last_seen = NOW() WHERE id = :id"),
                    {"id": existing["id"]},
                )
                resolved = 1

        return {"status": "evaluated", "raised": raised, "resolved": resolved,
                "breach": projection is not None}

    def _notify(self, conn, indicator_id, tenant_id, projection):
        name = conn.execute(
            text("SELECT name FROM indicators WHERE id = :id"), {"id": indicator_id},
        ).scalar() or str(indicator_id)
        subs = conn.execute(
            text("SELECT subscriber_role, subscriber_user FROM indicator_subscriptions "
                 "WHERE indicator_id = :id AND tenant_id = :tid"),
            {"id": indicator_id, "tid": tenant_id},
        ).mappings().all()
        watchers = ", ".join(s["subscriber_user"] or s["subscriber_role"] for s in subs) or "—"
        priority = "critical" if projection["confidence"] == "high" else "warning"
        msg = (f"ПРОГНОЗ: показатель '{name}' выйдет за коридор ({projection['direction']}) "
               f"≈{projection['ts']}, прогноз {projection['projected_value']:.2f}, "
               f"уверенность {projection['confidence']}. Действуйте заранее. Подписчики: {watchers}")
        try:
            from core.notifications import notify
            notify(msg, priority, event_type="predictive", tenant_id=tenant_id)
        except Exception as e:
            logger.error("predictive notify failed: %s", mask_secrets(str(e)))


def _points_json(points) -> str:
    norm = []
    for p in points:
        ts = p["ts"]
        norm.append({
            "ts": ts.isoformat() if hasattr(ts, "isoformat") else ts,
            "yhat": p["yhat"], "yhat_low": p.get("yhat_low"), "yhat_high": p.get("yhat_high"),
        })
    return json.dumps(norm)


predictive_engine = PredictiveEngine()
