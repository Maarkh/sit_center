# api/routes/recommendations.py
"""DSS M7 — Knowledge Base & Recommendation.

Two routers:
  * /playbooks  — manage the knowledge base (playbooks, actions, indicator scope);
  * /recommendations — generate ranked Next-Best-Action alternatives for a deviation
    or incident, then accept (→ instantiate the playbook's process) or dismiss.
All queries are tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional
from uuid import UUID
import json
from sqlalchemy import text

from core.database import get_engine
from core.recommendation_engine import recommendation_engine
from core.decision_engine import decision_engine
from core.process_engine import ProcessError
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets, logger
from api.schemas_dss import (
    PlaybookCreate, PlaybookUpdate, PlaybookRead, PlaybookListItem, PlaybookActionRead,
    RecommendationGenerateRequest, RecommendationRead, RecommendationDecision,
    OutcomeCreate, OutcomeRead, DecisionLogItem, PlaybookStats,
)

playbooks_router = APIRouter(prefix="/playbooks", tags=["DSS: Playbooks"])
recommendations_router = APIRouter(prefix="/recommendations", tags=["DSS: Recommendations"])


# ---------------------------------------------------------------------------
# Playbook helpers
# ---------------------------------------------------------------------------
def _load_playbook(conn, playbook_id, tenant_id) -> Optional[PlaybookRead]:
    pb = conn.execute(
        text("SELECT id, name, description, trigger_severity, trigger_direction, effect_score, "
             "process_template_id, is_active, created_at, updated_at "
             "FROM playbooks WHERE id = :id AND tenant_id = :tid"),
        {"id": playbook_id, "tid": tenant_id},
    ).mappings().first()
    if not pb:
        return None
    actions = conn.execute(
        text("SELECT id, action_order, action, checklist FROM playbook_actions "
             "WHERE playbook_id = :id ORDER BY action_order"),
        {"id": playbook_id},
    ).mappings().all()
    indicator_ids = conn.execute(
        text("SELECT indicator_id FROM playbook_indicators WHERE playbook_id = :id"),
        {"id": playbook_id},
    ).scalars().all()
    return PlaybookRead(
        **pb,
        indicator_ids=list(indicator_ids),
        actions=[PlaybookActionRead(id=a["id"], action_order=a["action_order"],
                                    action=a["action"], checklist=list(a["checklist"] or []))
                 for a in actions],
    )


def _insert_playbook_children(conn, playbook_id, tenant_id, data):
    for i, act in enumerate(data.actions):
        conn.execute(
            text("INSERT INTO playbook_actions (tenant_id, playbook_id, action_order, action, checklist) "
                 "VALUES (:tid, :pb, :ord, :act, CAST(:cl AS jsonb))"),
            {"tid": tenant_id, "pb": playbook_id, "ord": i, "act": act.action,
             "cl": json.dumps(act.checklist, ensure_ascii=False)},
        )
    for ind_id in dict.fromkeys(data.indicator_ids):
        owns = conn.execute(
            text("SELECT 1 FROM indicators WHERE id = :id AND tenant_id = :tid"),
            {"id": ind_id, "tid": tenant_id},
        ).first()
        if not owns:
            raise HTTPException(status_code=400, detail=f"indicator {ind_id} not found for this tenant")
        conn.execute(
            text("INSERT INTO playbook_indicators (playbook_id, indicator_id) VALUES (:pb, :ind) "
                 "ON CONFLICT DO NOTHING"),
            {"pb": playbook_id, "ind": ind_id},
        )


def _validate_template(conn, template_id, tenant_id):
    if template_id is None:
        return
    owns = conn.execute(
        text("SELECT 1 FROM process_templates WHERE id = :id AND tenant_id = :tid"),
        {"id": template_id, "tid": tenant_id},
    ).first()
    if not owns:
        raise HTTPException(status_code=400, detail="process_template_id not found for this tenant")


# ---------------------------------------------------------------------------
# Playbooks
# ---------------------------------------------------------------------------
@playbooks_router.post("", response_model=PlaybookRead, status_code=status.HTTP_201_CREATED,
                       summary="Create playbook")
@limiter.limit("30/minute")
def create_playbook(
    request: Request,
    data: PlaybookCreate,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            _validate_template(conn, data.process_template_id, current_user.tenant_id)
            pb_id = conn.execute(
                text("INSERT INTO playbooks (tenant_id, name, description, trigger_severity, "
                     "trigger_direction, effect_score, process_template_id, is_active) "
                     "VALUES (:tid, :name, :desc, :sev, :dir, :eff, :tmpl, :active) RETURNING id"),
                {"tid": current_user.tenant_id, "name": data.name, "desc": data.description,
                 "sev": data.trigger_severity, "dir": data.trigger_direction, "eff": data.effect_score,
                 "tmpl": data.process_template_id, "active": data.is_active},
            ).scalar()
            _insert_playbook_children(conn, pb_id, current_user.tenant_id, data)
            result = _load_playbook(conn, pb_id, current_user.tenant_id)
        log_audit(current_user.username, current_user.tenant_id, "create", "playbook", resource_id=str(pb_id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create playbook failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create playbook")


@playbooks_router.get("", response_model=List[PlaybookListItem], summary="List playbooks")
def list_playbooks(
    active_only: bool = Query(True),
    current_user: TokenData = Depends(require_permission("read:recommendations")),
):
    where = "tenant_id = :tid" + ("" if not active_only else " AND is_active = true")
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, trigger_severity, trigger_direction, effect_score, "
                 f"process_template_id, is_active FROM playbooks WHERE {where} ORDER BY name"),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [PlaybookListItem(**r) for r in rows]


@playbooks_router.get("/{playbook_id}", response_model=PlaybookRead, summary="Get playbook")
def get_playbook(
    playbook_id: UUID,
    current_user: TokenData = Depends(require_permission("read:recommendations")),
):
    engine = get_engine()
    with engine.connect() as conn:
        pb = _load_playbook(conn, playbook_id, current_user.tenant_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


@playbooks_router.put("/{playbook_id}", response_model=PlaybookRead, summary="Update playbook")
@limiter.limit("30/minute")
def update_playbook(
    request: Request,
    playbook_id: UUID,
    data: PlaybookUpdate,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            _validate_template(conn, data.process_template_id, current_user.tenant_id)
            updated = conn.execute(
                text("UPDATE playbooks SET name = :name, description = :desc, trigger_severity = :sev, "
                     "trigger_direction = :dir, effect_score = :eff, process_template_id = :tmpl, "
                     "is_active = :active WHERE id = :id AND tenant_id = :tid RETURNING id"),
                {"id": playbook_id, "tid": current_user.tenant_id, "name": data.name,
                 "desc": data.description, "sev": data.trigger_severity, "dir": data.trigger_direction,
                 "eff": data.effect_score, "tmpl": data.process_template_id, "active": data.is_active},
            ).first()
            if not updated:
                raise HTTPException(status_code=404, detail="Playbook not found")
            # Replace actions + scope wholesale (simplest consistent update).
            conn.execute(text("DELETE FROM playbook_actions WHERE playbook_id = :id"), {"id": playbook_id})
            conn.execute(text("DELETE FROM playbook_indicators WHERE playbook_id = :id"), {"id": playbook_id})
            _insert_playbook_children(conn, playbook_id, current_user.tenant_id, data)
            result = _load_playbook(conn, playbook_id, current_user.tenant_id)
        log_audit(current_user.username, current_user.tenant_id, "update", "playbook", resource_id=str(playbook_id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update playbook failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not update playbook")


@playbooks_router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete playbook")
@limiter.limit("10/minute")
def delete_playbook(
    request: Request,
    playbook_id: UUID,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM playbooks WHERE id = :id AND tenant_id = :tid"),
            {"id": playbook_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Playbook not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "playbook", resource_id=str(playbook_id))
    return


@playbooks_router.get("/{playbook_id}/stats", response_model=PlaybookStats,
                      summary="Playbook track record (M10 win-rate)")
def playbook_stats(
    playbook_id: UUID,
    current_user: TokenData = Depends(require_permission("read:recommendations")),
):
    return PlaybookStats(**decision_engine.playbook_stats(playbook_id, current_user.tenant_id))


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
_RECO_COLS = """
    r.id, r.deviation_id, r.incident_id, r.playbook_id, p.name AS playbook_name, r.rank,
    r.score, r.confidence, r.rationale, r.status, r.process_instance_id, r.decided_by,
    r.decided_at, r.created_at
"""


def _reco_row(row) -> RecommendationRead:
    return RecommendationRead(
        id=row["id"], deviation_id=row["deviation_id"], incident_id=row["incident_id"],
        playbook_id=row["playbook_id"], playbook_name=row["playbook_name"], rank=row["rank"],
        score=float(row["score"]), confidence=float(row["confidence"]), rationale=row["rationale"],
        status=row["status"], process_instance_id=row["process_instance_id"],
        decided_by=row["decided_by"], decided_at=row["decided_at"], created_at=row["created_at"],
    )


@recommendations_router.post("/generate", response_model=List[RecommendationRead],
                             summary="Generate Next-Best-Action recommendations")
@limiter.limit("30/minute")
def generate_recommendations(
    request: Request,
    data: RecommendationGenerateRequest,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    try:
        recommendation_engine.generate(
            current_user.tenant_id, deviation_id=data.deviation_id, incident_id=data.incident_id)
    except ProcessError as e:
        raise HTTPException(status_code=404, detail=str(e))
    log_audit(current_user.username, current_user.tenant_id, "generate", "recommendation",
              resource_id=str(data.deviation_id or data.incident_id))
    # Return the freshly persisted ranked list.
    return _list_recommendations(current_user.tenant_id, deviation_id=data.deviation_id,
                                 incident_id=data.incident_id)


@recommendations_router.get("", response_model=List[RecommendationRead], summary="List recommendations")
def list_recommendations(
    deviation_id: Optional[UUID] = Query(None),
    incident_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(require_permission("read:recommendations")),
):
    return _list_recommendations(current_user.tenant_id, deviation_id=deviation_id,
                                 incident_id=incident_id, status_filter=status_filter)


def _list_recommendations(tenant_id, *, deviation_id=None, incident_id=None, status_filter=None):
    where = ["r.tenant_id = :tid"]
    params = {"tid": tenant_id}
    if deviation_id is not None:
        where.append("r.deviation_id = :dev")
        params["dev"] = deviation_id
    if incident_id is not None:
        where.append("r.incident_id = :inc")
        params["inc"] = incident_id
    if status_filter:
        where.append("r.status = :st")
        params["st"] = status_filter
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT {_RECO_COLS} FROM recommendations r "
                 "LEFT JOIN playbooks p ON p.id = r.playbook_id "
                 f"WHERE {' AND '.join(where)} ORDER BY r.rank"),
            params,
        ).mappings().all()
    return [_reco_row(r) for r in rows]


@recommendations_router.post("/{recommendation_id}/accept", response_model=RecommendationRead,
                             summary="Accept recommendation (starts the process)")
@limiter.limit("30/minute")
def accept_recommendation(
    request: Request,
    recommendation_id: UUID,
    data: RecommendationDecision,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    try:
        recommendation_engine.accept(recommendation_id, current_user.tenant_id, user=current_user.username)
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    log_audit(current_user.username, current_user.tenant_id, "accept", "recommendation",
              resource_id=str(recommendation_id))
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {_RECO_COLS} FROM recommendations r "
                 "LEFT JOIN playbooks p ON p.id = r.playbook_id "
                 "WHERE r.id = :id AND r.tenant_id = :tid"),
            {"id": recommendation_id, "tid": current_user.tenant_id},
        ).mappings().first()
    return _reco_row(row)


@recommendations_router.post("/{recommendation_id}/dismiss", response_model=RecommendationRead,
                             summary="Dismiss recommendation")
@limiter.limit("60/minute")
def dismiss_recommendation(
    request: Request,
    recommendation_id: UUID,
    data: RecommendationDecision,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    engine = get_engine()
    with engine.begin() as conn:
        updated = conn.execute(
            text("UPDATE recommendations SET status = 'dismissed', decided_by = :user, decided_at = NOW() "
                 "WHERE id = :id AND tenant_id = :tid AND status = 'proposed' RETURNING id"),
            {"id": recommendation_id, "tid": current_user.tenant_id, "user": current_user.username},
        ).first()
        if not updated:
            raise HTTPException(status_code=409, detail="Recommendation not found or already decided")
        row = conn.execute(
            text(f"SELECT {_RECO_COLS} FROM recommendations r "
                 "LEFT JOIN playbooks p ON p.id = r.playbook_id WHERE r.id = :id"),
            {"id": recommendation_id},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "dismiss", "recommendation",
              resource_id=str(recommendation_id))
    return _reco_row(row)


# ---------------------------------------------------------------------------
# M10 — Decision Log & Outcomes
# ---------------------------------------------------------------------------
@recommendations_router.get("/decisions", response_model=List[DecisionLogItem],
                            summary="Decision log (accepted recommendations + outcomes)")
def decision_log(
    limit: int = Query(100, ge=1, le=500),
    current_user: TokenData = Depends(require_permission("read:recommendations")),
):
    return [DecisionLogItem(**d) for d in decision_engine.decision_log(current_user.tenant_id, limit=limit)]


@recommendations_router.post("/{recommendation_id}/outcome", response_model=OutcomeRead,
                             summary="Record the outcome of an accepted decision")
@limiter.limit("60/minute")
def record_outcome(
    request: Request,
    recommendation_id: UUID,
    data: OutcomeCreate,
    current_user: TokenData = Depends(require_permission("write:recommendations")),
):
    result = decision_engine.record_outcome(
        recommendation_id, current_user.tenant_id, resolved=data.resolved,
        effect_value=data.effect_value, note=data.note, user=current_user.username)
    if result is None:
        raise HTTPException(status_code=409, detail="Recommendation not found or not accepted")
    return OutcomeRead(**result)
