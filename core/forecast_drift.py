# core/forecast_drift.py
"""DSS M5 — forecast model-drift monitoring (Project / L3 quality control).

Scores persisted forecasts against the actuals that have since arrived: once a
forecast point's timestamp is in the past, the real value exists in
canonical_metrics, so we can measure how wrong the prediction was. Rolling
MAE/RMSE/MAPE per indicator-metric is recorded (forecast_accuracy) and a drift
notification fires when the error degrades past a threshold — the model-monitoring
the audit asked for, without standing up an MLflow server.

The error math (error_metrics / align_pairs) is pure and unit-tested; the DB
orchestration lives in ForecastDriftMonitor.
"""
import os
import bisect
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional

from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets

# Match a forecast point to the nearest actual within this tolerance (seconds).
DRIFT_TOLERANCE_SECONDS = int(os.environ.get("FORECAST_DRIFT_TOLERANCE_SEC", "600"))
# Raise a drift alert when MAPE exceeds this (percent) over at least N samples.
DRIFT_MAPE_ALERT = float(os.environ.get("FORECAST_DRIFT_MAPE_ALERT", "30"))
DRIFT_MIN_SAMPLES = int(os.environ.get("FORECAST_DRIFT_MIN_SAMPLES", "5"))


def error_metrics(pairs: List[Tuple[float, float]]) -> Dict[str, Any]:
    """(yhat, actual) pairs → {n, mae, rmse, mape}. MAPE skips actual==0 (None if all)."""
    n = len(pairs)
    if n == 0:
        return {"n": 0, "mae": None, "rmse": None, "mape": None}
    mae = sum(abs(yh - ac) for yh, ac in pairs) / n
    rmse = (sum((yh - ac) ** 2 for yh, ac in pairs) / n) ** 0.5
    pcts = [abs(yh - ac) / abs(ac) for yh, ac in pairs if ac != 0]
    mape = (sum(pcts) / len(pcts) * 100.0) if pcts else None
    return {
        "n": n,
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "mape": round(mape, 4) if mape is not None else None,
    }


def align_pairs(forecast_points: List[Tuple[datetime, float]],
                actual_series: List[Tuple[datetime, float]],
                tol_seconds: int = DRIFT_TOLERANCE_SECONDS) -> List[Tuple[float, float]]:
    """Match each forecast (ts, yhat) to the nearest actual (ts, value) within
    tol_seconds. actual_series must be sorted ascending by ts. Unmatched points are
    dropped. Returns [(yhat, actual)]."""
    if not actual_series:
        return []
    a_ts = [t for t, _ in actual_series]
    pairs: List[Tuple[float, float]] = []
    for ts, yhat in forecast_points:
        i = bisect.bisect_left(a_ts, ts)
        best_val: Optional[float] = None
        best_d: Optional[float] = None
        for j in (i - 1, i):
            if 0 <= j < len(actual_series):
                d = abs((actual_series[j][0] - ts).total_seconds())
                if best_d is None or d < best_d:
                    best_d, best_val = d, actual_series[j][1]
        if best_val is not None and best_d is not None and best_d <= tol_seconds:
            pairs.append((yhat, best_val))
    return pairs


def _parse_ts(raw) -> Optional[datetime]:
    """Forecast point ts is stored as an ISO string; normalise to aware UTC."""
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class ForecastDriftMonitor:
    def compute_tenant(self, tenant_id: str = "default", window_days: int = 7,
                       tol_seconds: int = DRIFT_TOLERANCE_SECONDS) -> dict:
        """Score every indicator-metric forecast in the window against actuals,
        persist the rolling error, and alert on drift. Returns a summary dict."""
        summary = {"series": 0, "scored": 0, "drift_alerts": 0}
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=window_days)
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT indicator_id, metric_name, points FROM forecasts "
                     "WHERE tenant_id = :tid AND generated_at >= :start"),
                {"tid": tenant_id, "start": window_start},
            ).mappings().all()

        # Group past forecast points by (indicator, metric).
        by_series: Dict[Tuple[Any, str], List[Tuple[datetime, float]]] = defaultdict(list)
        for r in rows:
            pts = r["points"]
            if isinstance(pts, str):
                try:
                    pts = json.loads(pts)
                except (ValueError, TypeError):
                    continue
            for p in pts or []:
                ts = _parse_ts(p.get("ts"))
                yhat = p.get("yhat")
                if ts is None or yhat is None or ts >= now:
                    continue
                by_series[(r["indicator_id"], r["metric_name"])].append((ts, float(yhat)))

        for (indicator_id, metric_name), fpoints in by_series.items():
            summary["series"] += 1
            try:
                scored = self._score_series(
                    tenant_id, indicator_id, metric_name, fpoints,
                    window_start, window_days, tol_seconds,
                )
                if scored:
                    summary["scored"] += 1
                    if scored.get("drift"):
                        summary["drift_alerts"] += 1
            except Exception as e:
                logger.error("drift scoring failed for %s/%s: %s",
                             indicator_id, metric_name, mask_secrets(str(e)))
        return summary

    def _score_series(self, tenant_id, indicator_id, metric_name, fpoints,
                      window_start, window_days, tol_seconds) -> Optional[dict]:
        engine = get_engine()
        with engine.connect() as conn:
            actuals = conn.execute(
                text("SELECT timestamp, value FROM canonical_metrics "
                     "WHERE tenant_id = :tid AND metric_name = :m AND timestamp >= :start "
                     "ORDER BY timestamp ASC"),
                {"tid": tenant_id, "m": metric_name, "start": window_start},
            ).all()
        series = [(t, float(v)) for t, v in actuals]
        pairs = align_pairs(fpoints, series, tol_seconds)
        m = error_metrics(pairs)
        if m["n"] == 0:
            return None

        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO forecast_accuracy (tenant_id, indicator_id, metric_name, "
                     "window_days, sample_size, mae, rmse, mape) "
                     "VALUES (:tid, :iid, :m, :w, :n, :mae, :rmse, :mape)"),
                {"tid": tenant_id, "iid": indicator_id, "m": metric_name, "w": window_days,
                 "n": m["n"], "mae": m["mae"], "rmse": m["rmse"], "mape": m["mape"]},
            )

        drift = m["mape"] is not None and m["n"] >= DRIFT_MIN_SAMPLES and m["mape"] > DRIFT_MAPE_ALERT
        if drift:
            try:
                from core.notifications import notify
                notify(f"Дрейф модели: прогноз '{metric_name}' за {window_days}д — "
                       f"MAPE {m['mape']:.1f}% (>{DRIFT_MAPE_ALERT:.0f}%, n={m['n']}); "
                       f"модель деградирует, нужна переобучка", "warning", tenant_id=tenant_id)
            except Exception as e:
                logger.error("drift notify failed: %s", mask_secrets(str(e)))
            logger.warning("forecast drift: %s/%s MAPE=%.1f%% n=%d",
                           indicator_id, metric_name, m["mape"], m["n"])
        return {**m, "drift": drift}


drift_monitor = ForecastDriftMonitor()
