# api/routes/situations.py
"""DSS M4 — Situation & Correlation.

Manage the indicator dependency graph, trigger/inspect correlation of deviations into
situations, and triage situations (impact + root-cause hypothesis). Correlation also
runs periodically via core.dss_tasks.correlate_situations_task. Tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text

from core.database import get_engine
from core.situation_engine import situation_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import logger, mask_secrets
from api.schemas_dss import (
    DependencyCreate, DependencyRead, SituationListItem, SituationRead,
    SituationStatusUpdate, CorrelateRequest, DeviationRead,
)

router = APIRouter(prefix="/situations", tags=["DSS: Situations"])

_DEV_COLS = """
    id, indicator_id, dimensions, direction, value, target_low, target_high, severity,
    status, periods, fingerprint, detected_at, last_seen, resolved_at, acknowledged_by,
    acknowledged_at
"""

_VALID_TRANSITIONS = {
    "open": {"investigating", "resolved", "closed"},
    "investigating": {"resolved", "closed", "open"},
    "resolved": {"closed", "investigating"},
    "closed": set(),
}


def _dev_read(row) -> DeviationRead:
    return DeviationRead(
        id=row["id"], indicator_id=row["indicator_id"], dimensions=row["dimensions"] or {},
        direction=row["direction"],
        value=float(row["value"]) if row["value"] is not None else None,
        target_low=float(row["target_low"]) if row["target_low"] is not None else None,
        target_high=float(row["target_high"]) if row["target_high"] is not None else None,
        severity=row["severity"], status=row["status"], periods=row["periods"],
        fingerprint=row["fingerprint"], detected_at=row["detected_at"], last_seen=row["last_seen"],
        resolved_at=row["resolved_at"], acknowledged_by=row["acknowledged_by"],
        acknowledged_at=row["acknowledged_at"],
    )


# ---------------------------------------------------------------------------
# Dependencies (influence graph) — defined before /{situation_id} to avoid clashes
# ---------------------------------------------------------------------------
@router.post("/dependencies", response_model=DependencyRead, status_code=status.HTTP_201_CREATED,
             summary="Add indicator dependency edge")
@limiter.limit("30/minute")
def create_dependency(
    request: Request,
    data: DependencyCreate,
    current_user: TokenData = Depends(require_permission("write:situations")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            for ind in (data.src_indicator_id, data.dst_indicator_id):
                owns = conn.execute(
                    text("SELECT 1 FROM indicators WHERE id = :id AND tenant_id = :tid"),
                    {"id": ind, "tid": current_user.tenant_id},
                ).first()
                if not owns:
                    raise HTTPException(status_code=400, detail=f"indicator {ind} not found for this tenant")
            row = conn.execute(
                text("INSERT INTO indicator_dependencies (tenant_id, src_indicator_id, "
                     "dst_indicator_id, weight) VALUES (:tid, :src, :dst, :w) "
                     "RETURNING id, src_indicator_id, dst_indicator_id, weight"),
                {"tid": current_user.tenant_id, "src": data.src_indicator_id,
                 "dst": data.dst_indicator_id, "w": data.weight},
            ).mappings().first()
        log_audit(current_user.username, current_user.tenant_id, "create", "dependency", resource_id=str(row["id"]))
        return DependencyRead(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create dependency failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create dependency (duplicate?)")


@router.get("/dependencies", response_model=List[DependencyRead], summary="List dependency edges")
def list_dependencies(
    current_user: TokenData = Depends(require_permission("read:situations")),
):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, src_indicator_id, dst_indicator_id, weight FROM indicator_dependencies "
                 "WHERE tenant_id = :tid ORDER BY created_at"),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [DependencyRead(**r) for r in rows]


@router.delete("/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete dependency edge")
@limiter.limit("20/minute")
def delete_dependency(
    request: Request,
    dependency_id: UUID,
    current_user: TokenData = Depends(require_permission("write:situations")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM indicator_dependencies WHERE id = :id AND tenant_id = :tid"),
            {"id": dependency_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Dependency not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "dependency", resource_id=str(dependency_id))
    return


# ---------------------------------------------------------------------------
# Correlation + Situations
# ---------------------------------------------------------------------------
@router.post("/correlate", summary="Run correlation now (deviations → situations)")
@limiter.limit("10/minute")
def run_correlation(
    request: Request,
    data: CorrelateRequest,
    current_user: TokenData = Depends(require_permission("write:situations")),
):
    summary = situation_engine.correlate_tenant(current_user.tenant_id, window_minutes=data.window_minutes)
    log_audit(current_user.username, current_user.tenant_id, "correlate", "situation")
    return summary


@router.get("/", response_model=List[SituationListItem], summary="List situations")
def list_situations(
    status_filter: Optional[str] = Query(None, alias="status"),
    active_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:situations")),
):
    where = ["tenant_id = :tid"]
    params = {"tid": current_user.tenant_id, "limit": limit, "offset": offset}
    if status_filter:
        where.append("status = :st")
        params["st"] = status_filter
    if active_only:
        where.append("status IN ('open', 'investigating')")
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, root_cause_indicator_id, impact_score, status, deviation_count, "
                 f"opened_at, closed_at FROM situations WHERE {' AND '.join(where)} "
                 "ORDER BY impact_score DESC, opened_at DESC LIMIT :limit OFFSET :offset"),
            params,
        ).mappings().all()
    return [SituationListItem(**r) for r in rows]


@router.get("/{situation_id}", response_model=SituationRead, summary="Get situation (with deviations)")
def get_situation(
    situation_id: UUID,
    current_user: TokenData = Depends(require_permission("read:situations")),
):
    engine = get_engine()
    with engine.connect() as conn:
        sit = conn.execute(
            text("SELECT id, title, root_cause_indicator_id, root_cause_hypothesis, impact_score, "
                 "status, deviation_count, opened_at, updated_at, closed_at FROM situations "
                 "WHERE id = :id AND tenant_id = :tid"),
            {"id": situation_id, "tid": current_user.tenant_id},
        ).mappings().first()
        if not sit:
            raise HTTPException(status_code=404, detail="Situation not found")
        devs = conn.execute(
            text(f"SELECT {_DEV_COLS} FROM deviations d "
                 "JOIN situation_deviations sd ON sd.deviation_id = d.id "
                 "WHERE sd.situation_id = :id ORDER BY d.detected_at"),
            {"id": situation_id},
        ).mappings().all()
    return SituationRead(**sit, deviations=[_dev_read(r) for r in devs])


@router.patch("/{situation_id}/status", response_model=SituationListItem, summary="Update situation status")
@limiter.limit("60/minute")
def update_situation_status(
    request: Request,
    situation_id: UUID,
    data: SituationStatusUpdate,
    current_user: TokenData = Depends(require_permission("write:situations")),
):
    engine = get_engine()
    with engine.begin() as conn:
        cur = conn.execute(
            text("SELECT status FROM situations WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
            {"id": situation_id, "tid": current_user.tenant_id},
        ).scalar()
        if cur is None:
            raise HTTPException(status_code=404, detail="Situation not found")
        if data.status != cur and data.status not in _VALID_TRANSITIONS.get(cur, set()):
            raise HTTPException(status_code=400, detail=f"Invalid transition {cur} → {data.status}")
        closed = data.status in ("resolved", "closed")
        row = conn.execute(
            text("UPDATE situations SET status = :st, "
                 "closed_at = CASE WHEN :closed THEN COALESCE(closed_at, NOW()) ELSE NULL END "
                 "WHERE id = :id RETURNING id, title, root_cause_indicator_id, impact_score, status, "
                 "deviation_count, opened_at, closed_at"),
            {"st": data.status, "closed": closed, "id": situation_id},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "update", "situation", resource_id=str(situation_id))
    return SituationListItem(**row)
