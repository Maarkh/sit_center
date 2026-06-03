# api/routes/processes.py
"""DSS M8 (MVP) — process / workflow engine endpoints.

Define a regulation as a ProcessTemplate (ordered steps), instantiate it against a
situation (incident or deviation), and drive each step: start → checklist → complete.
The wave engine (core/process_engine.py) advances sequential/parallel steps and
finishes the instance. Every query is tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional
from uuid import UUID
import json
from sqlalchemy import text

from core.database import get_engine
from core.process_engine import process_engine, ProcessError
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets, logger
from api.schemas_dss import (
    ProcessTemplateCreate, ProcessTemplateRead, ProcessTemplateListItem, ProcessStepRead,
    ProcessInstanceCreate, ProcessInstanceRead, ProcessInstanceListItem, StepAssignmentRead,
    StepStartRequest, ChecklistUpdateRequest, StepCompleteRequest,
)

router = APIRouter(prefix="/processes", tags=["DSS: Processes"])


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------
def _load_template(conn, template_id, tenant_id) -> Optional[ProcessTemplateRead]:
    tmpl = conn.execute(
        text("SELECT id, name, description, is_active, created_at, updated_at "
             "FROM process_templates WHERE id = :id AND tenant_id = :tid"),
        {"id": template_id, "tid": tenant_id},
    ).mappings().first()
    if not tmpl:
        return None
    steps = conn.execute(
        text("SELECT id, step_order, name, step_type, assignee_role, checklist, due_after_minutes "
             "FROM process_steps WHERE template_id = :id ORDER BY step_order, name"),
        {"id": template_id},
    ).mappings().all()
    return ProcessTemplateRead(
        **tmpl,
        steps=[ProcessStepRead(
            id=s["id"], step_order=s["step_order"], name=s["name"], step_type=s["step_type"],
            assignee_role=s["assignee_role"], checklist=list(s["checklist"] or []),
            due_after_minutes=s["due_after_minutes"],
        ) for s in steps],
    )


def _load_instance(conn, instance_id, tenant_id) -> Optional[ProcessInstanceRead]:
    inst = conn.execute(
        text("SELECT id, template_id, incident_id, deviation_id, title, status, started_by, "
             "started_at, completed_at FROM process_instances WHERE id = :id AND tenant_id = :tid"),
        {"id": instance_id, "tid": tenant_id},
    ).mappings().first()
    if not inst:
        return None
    rows = conn.execute(
        text("SELECT id, instance_id, step_id, step_order, step_type, name, assignee_role, "
             "assignee, checklist_state, status, report, due_at, escalated, started_at, "
             "activated_at, completed_at, completed_by FROM step_assignments "
             "WHERE instance_id = :id ORDER BY step_order, name"),
        {"id": instance_id},
    ).mappings().all()
    return ProcessInstanceRead(
        **inst,
        assignments=[StepAssignmentRead(**dict(r)) for r in rows],
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
@router.post("/templates", response_model=ProcessTemplateRead,
             status_code=status.HTTP_201_CREATED, summary="Create process template")
@limiter.limit("30/minute")
def create_template(
    request: Request,
    data: ProcessTemplateCreate,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            tmpl_id = conn.execute(
                text("INSERT INTO process_templates (tenant_id, name, description, is_active) "
                     "VALUES (:tid, :name, :desc, :active) RETURNING id"),
                {"tid": current_user.tenant_id, "name": data.name, "desc": data.description,
                 "active": data.is_active},
            ).scalar()
            for s in data.steps:
                conn.execute(
                    text("INSERT INTO process_steps (tenant_id, template_id, step_order, name, "
                         "step_type, assignee_role, checklist, due_after_minutes) "
                         "VALUES (:tid, :tmpl, :ord, :name, :type, :role, CAST(:cl AS jsonb), :due)"),
                    {"tid": current_user.tenant_id, "tmpl": tmpl_id, "ord": s.step_order,
                     "name": s.name, "type": s.step_type, "role": s.assignee_role,
                     "cl": json.dumps(s.checklist, ensure_ascii=False), "due": s.due_after_minutes},
                )
            result = _load_template(conn, tmpl_id, current_user.tenant_id)
        log_audit(current_user.username, current_user.tenant_id, "create", "process_template",
                  resource_id=str(tmpl_id))
        return result
    except Exception as e:
        logger.error("create template failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create template")


@router.get("/templates", response_model=List[ProcessTemplateListItem], summary="List templates")
def list_templates(
    active_only: bool = Query(True),
    current_user: TokenData = Depends(require_permission("read:processes")),
):
    where = "tenant_id = :tid" + ("" if not active_only else " AND t.is_active = true")
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT t.id, t.name, t.description, t.is_active, t.created_at, "
                "COUNT(s.id) AS step_count FROM process_templates t "
                "LEFT JOIN process_steps s ON s.template_id = t.id "
                f"WHERE t.{where} GROUP BY t.id ORDER BY t.name"
            ),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [ProcessTemplateListItem(**r) for r in rows]


@router.get("/templates/{template_id}", response_model=ProcessTemplateRead, summary="Get template")
def get_template(
    template_id: UUID,
    current_user: TokenData = Depends(require_permission("read:processes")),
):
    engine = get_engine()
    with engine.connect() as conn:
        tmpl = _load_template(conn, template_id, current_user.tenant_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete template")
@limiter.limit("10/minute")
def delete_template(
    request: Request,
    template_id: UUID,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM process_templates WHERE id = :id AND tenant_id = :tid"),
            {"id": template_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Template not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "process_template",
              resource_id=str(template_id))
    return


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------
@router.post("/instances", response_model=ProcessInstanceRead,
             status_code=status.HTTP_201_CREATED, summary="Start a process instance")
@limiter.limit("30/minute")
def create_instance(
    request: Request,
    data: ProcessInstanceCreate,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    try:
        inst_id = process_engine.instantiate(
            data.template_id, current_user.tenant_id,
            started_by=current_user.username, title=data.title,
            incident_id=data.incident_id, deviation_id=data.deviation_id,
        )
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    engine = get_engine()
    with engine.connect() as conn:
        return _load_instance(conn, inst_id, current_user.tenant_id)


@router.get("/instances", response_model=List[ProcessInstanceListItem], summary="List instances")
def list_instances(
    status_filter: Optional[str] = Query(None, alias="status"),
    incident_id: Optional[int] = Query(None),
    deviation_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:processes")),
):
    where = ["tenant_id = :tid"]
    params = {"tid": current_user.tenant_id, "limit": limit, "offset": offset}
    if status_filter:
        where.append("status = :st")
        params["st"] = status_filter
    if incident_id is not None:
        where.append("incident_id = :inc")
        params["inc"] = incident_id
    if deviation_id is not None:
        where.append("deviation_id = :dev")
        params["dev"] = deviation_id
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, template_id, title, status, incident_id, deviation_id, started_at, "
                 f"completed_at FROM process_instances WHERE {' AND '.join(where)} "
                 "ORDER BY started_at DESC LIMIT :limit OFFSET :offset"),
            params,
        ).mappings().all()
    return [ProcessInstanceListItem(**r) for r in rows]


@router.get("/instances/{instance_id}", response_model=ProcessInstanceRead,
            summary="Get instance (timeline)")
def get_instance(
    instance_id: UUID,
    current_user: TokenData = Depends(require_permission("read:processes")),
):
    engine = get_engine()
    with engine.connect() as conn:
        inst = _load_instance(conn, instance_id, current_user.tenant_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return inst


@router.post("/instances/{instance_id}/cancel", status_code=status.HTTP_204_NO_CONTENT,
             summary="Cancel instance")
@limiter.limit("20/minute")
def cancel_instance(
    request: Request,
    instance_id: UUID,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    try:
        process_engine.cancel_instance(instance_id, current_user.tenant_id, user=current_user.username)
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return


# ---------------------------------------------------------------------------
# Step assignment actions
# ---------------------------------------------------------------------------
@router.post("/assignments/{assignment_id}/start", response_model=StepAssignmentRead,
             summary="Start working on a step")
@limiter.limit("60/minute")
def start_assignment(
    request: Request,
    assignment_id: UUID,
    data: StepStartRequest,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    try:
        a = process_engine.start_step(assignment_id, current_user.tenant_id,
                                      user=current_user.username, assignee=data.assignee)
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return StepAssignmentRead(**a)


@router.patch("/assignments/{assignment_id}/checklist", response_model=StepAssignmentRead,
              summary="Update step checklist")
@limiter.limit("120/minute")
def update_assignment_checklist(
    request: Request,
    assignment_id: UUID,
    data: ChecklistUpdateRequest,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    try:
        a = process_engine.update_checklist(
            assignment_id, current_user.tenant_id,
            [item.model_dump() for item in data.checklist_state],
        )
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return StepAssignmentRead(**a)


@router.post("/assignments/{assignment_id}/complete", response_model=StepAssignmentRead,
             summary="Complete a step (advances the process)")
@limiter.limit("60/minute")
def complete_assignment(
    request: Request,
    assignment_id: UUID,
    data: StepCompleteRequest,
    current_user: TokenData = Depends(require_permission("write:processes")),
):
    try:
        a = process_engine.complete_step(assignment_id, current_user.tenant_id,
                                         user=current_user.username, report=data.report, force=data.force)
    except ProcessError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return StepAssignmentRead(**a)
