# api/routes/deviations.py
"""DSS M3 — read/triage of corridor deviations and chronicles.

Deviations are produced by the evaluation loop (core/deviation_engine.py, run from
the Celery beat task). These endpoints expose them for the cockpit and let an
operator acknowledge / resolve an active episode. Every query is tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text

from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from api.schemas_dss import DeviationRead, DeviationAck, ChronicleRead

router = APIRouter(prefix="/deviations", tags=["DSS: Deviations"])

_DEV_COLS = """
    id, indicator_id, dimensions, direction, value, target_low, target_high,
    severity, status, periods, fingerprint, detected_at, last_seen, resolved_at,
    acknowledged_by, acknowledged_at
"""


def _row_to_deviation(row) -> DeviationRead:
    return DeviationRead(
        id=row["id"],
        indicator_id=row["indicator_id"],
        dimensions=row["dimensions"] or {},
        direction=row["direction"],
        value=float(row["value"]) if row["value"] is not None else None,
        target_low=float(row["target_low"]) if row["target_low"] is not None else None,
        target_high=float(row["target_high"]) if row["target_high"] is not None else None,
        severity=row["severity"],
        status=row["status"],
        periods=row["periods"],
        fingerprint=row["fingerprint"],
        detected_at=row["detected_at"],
        last_seen=row["last_seen"],
        resolved_at=row["resolved_at"],
        acknowledged_by=row["acknowledged_by"],
        acknowledged_at=row["acknowledged_at"],
    )


@router.get("/", response_model=List[DeviationRead], summary="List deviations")
def list_deviations(
    indicator_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    active_only: bool = Query(False, description="only open|acknowledged episodes"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:deviations")),
):
    where = ["tenant_id = :tid"]
    params = {"tid": current_user.tenant_id, "limit": limit, "offset": offset}
    if indicator_id is not None:
        where.append("indicator_id = :iid")
        params["iid"] = indicator_id
    if status_filter:
        where.append("status = :st")
        params["st"] = status_filter
    if severity:
        where.append("severity = :sev")
        params["sev"] = severity
    if active_only:
        where.append("status <> 'resolved'")

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"SELECT {_DEV_COLS} FROM deviations WHERE {' AND '.join(where)} "
                f"ORDER BY detected_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
    return [_row_to_deviation(r) for r in rows]


@router.get("/{deviation_id}", response_model=DeviationRead, summary="Get deviation")
def get_deviation(
    deviation_id: UUID,
    current_user: TokenData = Depends(require_permission("read:deviations")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {_DEV_COLS} FROM deviations WHERE id = :id AND tenant_id = :tid"),
            {"id": deviation_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Deviation not found")
    return _row_to_deviation(row)


@router.post("/{deviation_id}/acknowledge", response_model=DeviationRead, summary="Acknowledge deviation")
@limiter.limit("60/minute")
def acknowledge_deviation(
    request: Request,
    deviation_id: UUID,
    data: DeviationAck,
    current_user: TokenData = Depends(require_permission("write:deviations")),
):
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "UPDATE deviations SET status = 'acknowledged', acknowledged_by = :who, "
                "acknowledged_at = NOW() WHERE id = :id AND tenant_id = :tid AND status = 'open' "
                f"RETURNING {_DEV_COLS}"
            ),
            {"id": deviation_id, "tid": current_user.tenant_id, "who": current_user.username},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=409, detail="Deviation not found or not in 'open' state")
    log_audit(current_user.username, current_user.tenant_id, "acknowledge", "deviation",
              resource_id=str(deviation_id))
    return _row_to_deviation(row)


@router.post("/{deviation_id}/resolve", response_model=DeviationRead, summary="Resolve deviation")
@limiter.limit("60/minute")
def resolve_deviation(
    request: Request,
    deviation_id: UUID,
    data: DeviationAck,
    current_user: TokenData = Depends(require_permission("write:deviations")),
):
    """Manually close an episode. The next evaluation cycle will re-open a fresh
    episode if the indicator is still outside its corridor."""
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "UPDATE deviations SET status = 'resolved', resolved_at = NOW(), last_seen = NOW() "
                "WHERE id = :id AND tenant_id = :tid AND status <> 'resolved' "
                f"RETURNING {_DEV_COLS}"
            ),
            {"id": deviation_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=409, detail="Deviation not found or already resolved")
    log_audit(current_user.username, current_user.tenant_id, "resolve", "deviation",
              resource_id=str(deviation_id))
    return _row_to_deviation(row)


@router.get("/chronicles/list", response_model=List[ChronicleRead], summary="List chronicles")
def list_chronicles(
    indicator_id: Optional[UUID] = Query(None),
    min_episodes: int = Query(1, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: TokenData = Depends(require_permission("read:deviations")),
):
    where = ["tenant_id = :tid", "episodes >= :minep"]
    params = {"tid": current_user.tenant_id, "minep": min_episodes, "limit": limit}
    if indicator_id is not None:
        where.append("indicator_id = :iid")
        params["iid"] = indicator_id
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, indicator_id, fingerprint, episodes, total_periods, max_periods, "
                f"first_seen, last_seen FROM chronicles WHERE {' AND '.join(where)} "
                "ORDER BY total_periods DESC LIMIT :limit"
            ),
            params,
        ).mappings().all()
    return [ChronicleRead(**r) for r in rows]
