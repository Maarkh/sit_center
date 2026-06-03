# api/routes/predictions.py
"""DSS M5 — Forecasting & Predictive Alerts.

Read/triage predictive alerts (projected corridor breaches), fetch forecast snapshots,
and trigger an on-demand forecast+evaluation for an indicator. The periodic evaluation
runs from core.dss_tasks.predict_indicators_task. Every query is tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text

from core.database import get_engine
from core.predictive_engine import predictive_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import logger, mask_secrets
from api.schemas_dss import PredictiveAlertRead, PredictiveAlertAck, ForecastRead, PredictRunRequest

router = APIRouter(prefix="/predictions", tags=["DSS: Predictive"])

_PA_COLS = """
    id, indicator_id, direction, projected_value, target_low, target_high, breach_eta,
    horizon_hours, confidence, status, fingerprint, created_at, last_seen, resolved_at,
    acknowledged_by, acknowledged_at
"""


def _row_to_alert(row) -> PredictiveAlertRead:
    return PredictiveAlertRead(
        id=row["id"], indicator_id=row["indicator_id"], direction=row["direction"],
        projected_value=float(row["projected_value"]) if row["projected_value"] is not None else None,
        target_low=float(row["target_low"]) if row["target_low"] is not None else None,
        target_high=float(row["target_high"]) if row["target_high"] is not None else None,
        breach_eta=row["breach_eta"], horizon_hours=row["horizon_hours"],
        confidence=row["confidence"], status=row["status"], fingerprint=row["fingerprint"],
        created_at=row["created_at"], last_seen=row["last_seen"], resolved_at=row["resolved_at"],
        acknowledged_by=row["acknowledged_by"], acknowledged_at=row["acknowledged_at"],
    )


@router.post("/run", summary="Forecast + evaluate one indicator on demand")
@limiter.limit("10/minute")
def run_prediction(
    request: Request,
    data: PredictRunRequest,
    current_user: TokenData = Depends(require_permission("write:predictions")),
):
    """Triggers a Prophet forecast for the indicator's single source metric and
    evaluates it against the corridor. Returns the engine status (may be skipped when
    ML libs / data are unavailable)."""
    try:
        result = predictive_engine.forecast_and_evaluate(
            data.indicator_id, current_user.tenant_id, data.horizon_hours)
    except Exception as e:
        logger.error("on-demand prediction failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=500, detail="Prediction failed")
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Indicator not found or inactive")
    log_audit(current_user.username, current_user.tenant_id, "predict", "indicator",
              resource_id=str(data.indicator_id))
    return result


@router.get("/", response_model=List[PredictiveAlertRead], summary="List predictive alerts")
def list_predictive_alerts(
    indicator_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    active_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    current_user: TokenData = Depends(require_permission("read:predictions")),
):
    where = ["tenant_id = :tid"]
    params = {"tid": current_user.tenant_id, "limit": limit}
    if indicator_id is not None:
        where.append("indicator_id = :iid")
        params["iid"] = indicator_id
    if status_filter:
        where.append("status = :st")
        params["st"] = status_filter
    if active_only:
        where.append("status <> 'resolved'")
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT {_PA_COLS} FROM predictive_alerts WHERE {' AND '.join(where)} "
                 "ORDER BY breach_eta NULLS LAST, created_at DESC LIMIT :limit"),
            params,
        ).mappings().all()
    return [_row_to_alert(r) for r in rows]


@router.get("/forecasts/{indicator_id}/latest", response_model=ForecastRead,
            summary="Latest forecast snapshot for an indicator")
def latest_forecast(
    indicator_id: UUID,
    current_user: TokenData = Depends(require_permission("read:predictions")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, indicator_id, metric_name, horizon_hours, model_version, "
                 "generated_at, points FROM forecasts WHERE indicator_id = :id AND tenant_id = :tid "
                 "ORDER BY generated_at DESC LIMIT 1"),
            {"id": indicator_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No forecast for this indicator")
    return ForecastRead(
        id=row["id"], indicator_id=row["indicator_id"], metric_name=row["metric_name"],
        horizon_hours=row["horizon_hours"], model_version=row["model_version"],
        generated_at=row["generated_at"], points=row["points"] or [],
    )


@router.get("/{alert_id}", response_model=PredictiveAlertRead, summary="Get predictive alert")
def get_predictive_alert(
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("read:predictions")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {_PA_COLS} FROM predictive_alerts WHERE id = :id AND tenant_id = :tid"),
            {"id": alert_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Predictive alert not found")
    return _row_to_alert(row)


@router.post("/{alert_id}/acknowledge", response_model=PredictiveAlertRead, summary="Acknowledge")
@limiter.limit("60/minute")
def acknowledge_predictive_alert(
    request: Request,
    alert_id: UUID,
    data: PredictiveAlertAck,
    current_user: TokenData = Depends(require_permission("write:predictions")),
):
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("UPDATE predictive_alerts SET status = 'acknowledged', acknowledged_by = :who, "
                 "acknowledged_at = NOW() WHERE id = :id AND tenant_id = :tid AND status = 'open' "
                 f"RETURNING {_PA_COLS}"),
            {"id": alert_id, "tid": current_user.tenant_id, "who": current_user.username},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=409, detail="Alert not found or not in 'open' state")
    log_audit(current_user.username, current_user.tenant_id, "acknowledge", "predictive_alert",
              resource_id=str(alert_id))
    return _row_to_alert(row)


@router.post("/{alert_id}/resolve", response_model=PredictiveAlertRead, summary="Resolve")
@limiter.limit("60/minute")
def resolve_predictive_alert(
    request: Request,
    alert_id: UUID,
    data: PredictiveAlertAck,
    current_user: TokenData = Depends(require_permission("write:predictions")),
):
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("UPDATE predictive_alerts SET status = 'resolved', resolved_at = NOW(), "
                 "last_seen = NOW() WHERE id = :id AND tenant_id = :tid AND status <> 'resolved' "
                 f"RETURNING {_PA_COLS}"),
            {"id": alert_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=409, detail="Alert not found or already resolved")
    log_audit(current_user.username, current_user.tenant_id, "resolve", "predictive_alert",
              resource_id=str(alert_id))
    return _row_to_alert(row)
