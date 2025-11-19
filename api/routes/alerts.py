# api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID
from api.schemas import AlertRead
from sqlalchemy import text
from core.database import get_engine
from api.auth import get_current_user, TokenData
from config import mask_secrets

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _row_to_alert(row) -> AlertRead:
    return AlertRead(
        id=row["id"],
        rule_id=row["rule_id"],
        ml_config_id=row["ml_config_id"],
        metric_name=row["metric_name"],
        dimensions=row["dimensions"] or {},
        value=row["value"],
        event_time=row["event_time"],
        detected_at=row["detected_at"],
        status=row["status"],
        sent=row["sent"],
        fingerprint=row["fingerprint"]
    )


@router.get("/", response_model=List[AlertRead])
def list_alerts(
    status: str = Query(None, enum=["firing", "resolved"]),
    metric_name: str = None, # type: ignore
    dimension_key: str = None, # type: ignore
    dimension_value: str = None, # type: ignore
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(get_current_user) 
):
    engine = get_engine()
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status # type: ignore
    if metric_name:
        where_clauses.append("metric_name = :metric_name")
        params["metric_name"] = metric_name # type: ignore
    if dimension_key and dimension_value:
        where_clauses.append(f"dimensions->>'{dimension_key}' = :dim_val")
        params["dim_val"] = dimension_value # type: ignore

    where = " AND ".join(where_clauses)
    if where:
        where = "WHERE " + where

    query = text(f"""
        SELECT id, rule_id, ml_config_id, metric_name, dimensions, value,
               event_time, detected_at, status, sent, fingerprint
        FROM alert_events
        {where}
        ORDER BY event_time DESC
        LIMIT :limit OFFSET :offset
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [_row_to_alert(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: UUID):
    engine = get_engine()
    query = text("""
        SELECT id, rule_id, ml_config_id, metric_name, dimensions, value,
               event_time, detected_at, status, sent, fingerprint
        FROM alert_events
        WHERE id = :alert_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"alert_id": alert_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")
            return _row_to_alert(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))


@router.post("/{alert_id}/suppress", status_code=204)
def suppress_alert(alert_id: UUID, minutes: int = 60, current_user: TokenData = Depends(get_current_user)):
    """Ручное подавление алерта по его fingerprint"""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT fingerprint FROM alert_events WHERE id = :id"),
                {"id": alert_id}
            ).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")

            from core.alerts import suppress_alert as _suppress
            _suppress(row["fingerprint"], minutes)
            return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))