# api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from api.schemas import AlertRead
from sqlalchemy import text
from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets

router = APIRouter(prefix="/alerts", tags=["Alerts"])


ALERT_FIELDS = """id, rule_id, ml_config_id, metric_name, dimensions, value,
    event_time, detected_at, status, sent, fingerprint,
    acknowledged_by, acknowledged_at, resolved_by, tenant_id"""


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
        fingerprint=row["fingerprint"],
        acknowledged_by=row.get("acknowledged_by"),
        acknowledged_at=row.get("acknowledged_at"),
        resolved_by=row.get("resolved_by"),
    )


@router.get("/", response_model=List[AlertRead], summary="List alert events")
def list_alerts(
    status: str = Query(None, enum=["firing", "acknowledged", "resolved"]),
    metric_name: str = None,  # type: ignore
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    where_clauses = ["tenant_id = :tenant_id"]
    params = {"limit": limit, "offset": offset, "tenant_id": current_user.tenant_id}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status  # type: ignore
    if metric_name:
        where_clauses.append("metric_name = :metric_name")
        params["metric_name"] = metric_name  # type: ignore

    where = "WHERE " + " AND ".join(where_clauses)

    query = text(f"""
        SELECT {ALERT_FIELDS}
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
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.get("/{alert_id}", response_model=AlertRead, summary="Get alert by ID")
def get_alert(
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    query = text(f"""
        SELECT {ALERT_FIELDS}
        FROM alert_events
        WHERE id = :alert_id AND tenant_id = :tenant_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"alert_id": alert_id, "tenant_id": current_user.tenant_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")
            return _row_to_alert(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.post("/{alert_id}/suppress", status_code=204, summary="Suppress alert by fingerprint")
@limiter.limit("30/minute")
def suppress_alert(
    request: Request,
    alert_id: UUID,
    minutes: int = 60,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT fingerprint FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")

            from core.alerts import suppress_alert as _suppress
            _suppress(row["fingerprint"], minutes)

        log_audit(current_user.username, current_user.tenant_id, "suppress", "alert", resource_id=str(alert_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.post("/{alert_id}/acknowledge", response_model=AlertRead, summary="Acknowledge firing alert")
@limiter.limit("30/minute")
def acknowledge_alert(
    request: Request,
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()

            if not row:
                raise HTTPException(404, "Alert not found")
            if row["status"] not in ("firing",):
                raise HTTPException(400, f"Cannot acknowledge alert in status '{row['status']}'")

            conn.execute(
                text("""
                    UPDATE alert_events SET
                        status = 'acknowledged',
                        acknowledged_by = :user,
                        acknowledged_at = :now
                    WHERE id = :id
                """),
                {"id": alert_id, "user": current_user.username, "now": now},
            )

            result = conn.execute(
                text(f"SELECT {ALERT_FIELDS} FROM alert_events WHERE id = :id"),
                {"id": alert_id},
            ).mappings().first()

        log_audit(current_user.username, current_user.tenant_id, "acknowledge", "alert", resource_id=str(alert_id))
        return _row_to_alert(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))


@router.post("/{alert_id}/resolve", response_model=AlertRead, summary="Resolve alert")
@limiter.limit("30/minute")
def resolve_alert(
    request: Request,
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()

            if not row:
                raise HTTPException(404, "Alert not found")
            if row["status"] == "resolved":
                raise HTTPException(400, "Alert already resolved")

            conn.execute(
                text("""
                    UPDATE alert_events SET
                        status = 'resolved',
                        resolved_at = :now,
                        resolved_by = :user
                    WHERE id = :id
                """),
                {"id": alert_id, "user": current_user.username, "now": now},
            )

            result = conn.execute(
                text(f"SELECT {ALERT_FIELDS} FROM alert_events WHERE id = :id"),
                {"id": alert_id},
            ).mappings().first()

        log_audit(current_user.username, current_user.tenant_id, "resolve", "alert", resource_id=str(alert_id))
        return _row_to_alert(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))
