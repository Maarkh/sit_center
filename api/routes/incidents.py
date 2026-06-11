# api/routes/incidents.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import text
from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from api.schemas import (
    IncidentCreate, IncidentRead, IncidentStatusUpdate,
    IncidentAssign, IncidentCommentCreate, IncidentCommentRead,
    IncidentListResponse, SlaPolicyCreate, SlaPolicyRead,
)
from config import mask_secrets, logger
from core.audit import log_audit
from api.limiter import limiter

router = APIRouter(prefix="/incidents", tags=["Incidents"])

VALID_TRANSITIONS = {
    "new": {"in_progress", "escalated", "closed"},
    "in_progress": {"escalated", "resolved", "closed"},
    "escalated": {"in_progress", "resolved", "closed"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}

INCIDENT_COLUMNS = """
    id, alert_message, metric, region, value, priority, status, detected_at,
    assigned_to, started_at, resolved_at, closed_at, description, alert_event_id,
    response_deadline, resolution_deadline, response_breached, resolution_breached,
    escalation_level, last_escalated_at, external_id, external_system, external_url
"""


def _row_to_incident(row) -> IncidentRead:
    return IncidentRead(
        id=row["id"],
        alert_message=row["alert_message"],
        metric=row["metric"],
        region=row["region"],
        value=row["value"],
        priority=row["priority"],
        status=row["status"],
        detected_at=row["detected_at"],
        assigned_to=row["assigned_to"],
        started_at=row["started_at"],
        resolved_at=row["resolved_at"],
        closed_at=row["closed_at"],
        description=row["description"],
        alert_event_id=row["alert_event_id"],
        response_deadline=row["response_deadline"],
        resolution_deadline=row["resolution_deadline"],
        response_breached=row["response_breached"] or False,
        resolution_breached=row["resolution_breached"] or False,
        escalation_level=row["escalation_level"] or 0,
        last_escalated_at=row["last_escalated_at"],
        external_id=row.get("external_id"),
        external_system=row.get("external_system"),
        external_url=row.get("external_url"),
    )


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    breached: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    where = ["tenant_id = :tenant_id"]
    params = {"tenant_id": current_user.tenant_id, "limit": limit, "offset": offset}

    if status:
        where.append("status = :status")
        params["status"] = status
    if priority:
        where.append("priority = :priority")
        params["priority"] = priority
    if assigned_to:
        where.append("assigned_to = :assigned_to")
        params["assigned_to"] = assigned_to
    if metric:
        where.append("metric = :metric")
        params["metric"] = metric
    if region:
        where.append("region = :region")
        params["region"] = region
    if active is True:
        # "open" on the dashboard = anything not yet resolved/closed (multi-status)
        where.append("status NOT IN ('resolved', 'closed')")
    if breached is True:
        where.append("(response_breached = true OR resolution_breached = true)")

    where_clause = " AND ".join(where)
    engine = get_engine()

    try:
        with engine.connect() as conn:
            total = conn.execute(
                text(f"SELECT COUNT(*) FROM incidents WHERE {where_clause}"), params
            ).scalar()

            rows = conn.execute(
                text(f"""
                    SELECT {INCIDENT_COLUMNS}
                    FROM incidents WHERE {where_clause}
                    ORDER BY detected_at DESC LIMIT :limit OFFSET :offset
                """),
                params,
            ).mappings().all()

            return IncidentListResponse(
                items=[_row_to_incident(r) for r in rows],
                total=total,
            )
    except Exception:
        logger.exception("Error listing incidents")
        raise HTTPException(500, "Failed to list incidents")


@router.post("/", response_model=IncidentRead, status_code=201)
@limiter.limit("30/minute")
def create_incident(
    request: Request,
    data: IncidentCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    now = datetime.now(timezone.utc)
    engine = get_engine()

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(f"""
                    INSERT INTO incidents (
                        alert_message, metric, region, value, priority, status,
                        detected_at, assigned_to, description, alert_event_id, tenant_id
                    ) VALUES (
                        :alert_message, :metric, :region, :value, :priority, 'new',
                        :detected_at, :assigned_to, :description, :alert_event_id, :tenant_id
                    )
                    RETURNING {INCIDENT_COLUMNS}
                """),
                {
                    "alert_message": data.alert_message,
                    "metric": data.metric,
                    "region": data.region,
                    "value": data.value,
                    "priority": data.priority,
                    "detected_at": now,
                    "assigned_to": data.assigned_to,
                    "description": data.description,
                    "alert_event_id": data.alert_event_id,
                    "tenant_id": current_user.tenant_id,
                },
            ).mappings().first()

        incident = _row_to_incident(row)

        # Apply SLA policy
        try:
            from core.sla_service import apply_sla_to_incident
            apply_sla_to_incident(incident.id, current_user.tenant_id, data.priority, now)
        except Exception as e:
            logger.warning(f"Failed to apply SLA: {e}")

        # Assign default escalation chain
        try:
            with engine.begin() as conn:
                chain = conn.execute(
                    text("""
                        SELECT id FROM escalation_chains
                        WHERE tenant_id = :tid AND is_active = true
                        ORDER BY created_at LIMIT 1
                    """),
                    {"tid": current_user.tenant_id},
                ).mappings().first()
                if chain:
                    conn.execute(
                        text("UPDATE incidents SET escalation_chain_id = :cid WHERE id = :id"),
                        {"cid": chain["id"], "id": incident.id},
                    )
        except Exception as e:
            logger.warning(f"Failed to assign escalation chain: {e}")

        log_audit(current_user.username, current_user.tenant_id, "create", "incident", resource_id=str(incident.id))

        # Push to i-doit
        try:
            from core.idoit_service import push_incident_create
            push_incident_create(incident.id)
        except Exception as e:
            logger.warning(f"i-doit push failed: {e}")

        # Re-read to get SLA + i-doit fields
        with engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id AND tenant_id = :tid"),
                {"id": incident.id, "tid": current_user.tenant_id},
            ).mappings().first()
        return _row_to_incident(row)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating incident")
        raise HTTPException(500, "Failed to create incident")


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"""
                SELECT {INCIDENT_COLUMNS} FROM incidents
                WHERE id = :id AND tenant_id = :tid
            """),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

    if not row:
        raise HTTPException(404, "Incident not found")
    return _row_to_incident(row)


@router.patch("/{incident_id}/status", response_model=IncidentRead)
@limiter.limit("30/minute")
def update_incident_status(
    request: Request,
    incident_id: int,
    data: IncidentStatusUpdate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    # Lock the row and perform check-then-update atomically to avoid lost updates
    # on concurrent status changes (race condition / SLA timer desync).
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT status FROM incidents WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

        if not row:
            raise HTTPException(404, "Incident not found")

        current_status = row["status"]
        if data.status not in VALID_TRANSITIONS.get(current_status, set()):
            raise HTTPException(
                400,
                f"Cannot transition from '{current_status}' to '{data.status}'. "
                f"Allowed: {VALID_TRANSITIONS.get(current_status, set())}",
            )

        updates = ["status = :new_status"]
        params = {"id": incident_id, "new_status": data.status}

        if data.status == "in_progress" and current_status == "new":
            updates.append("started_at = :now")
            params["now"] = now
        elif data.status == "resolved":
            updates.append("resolved_at = :now")
            params["now"] = now
        elif data.status == "closed":
            updates.append("closed_at = :now")
            params["now"] = now

        conn.execute(
            text(f"UPDATE incidents SET {', '.join(updates)} WHERE id = :id"),
            params,
        )

        # Add comment for status change (same transaction)
        if data.comment:
            conn.execute(
                text("""
                    INSERT INTO incident_comments (incident_id, author, content)
                    VALUES (:iid, :author, :content)
                """),
                {"iid": incident_id, "author": current_user.username, "content": data.comment},
            )

    log_audit(
        current_user.username, current_user.tenant_id, "status_change", "incident",
        resource_id=str(incident_id),
        changes={"from": current_status, "to": data.status},
    )

    # Sync to i-doit
    try:
        from core.idoit_service import push_status_update
        push_status_update(incident_id, data.status)
    except Exception as e:
        logger.warning(f"i-doit status sync failed: {e}")

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()
    return _row_to_incident(row)


@router.patch("/{incident_id}/assign", response_model=IncidentRead)
def assign_incident(
    incident_id: int,
    data: IncidentAssign,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()

    # Lock the row so the existence check and the update are atomic.
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

        if not exists:
            raise HTTPException(404, "Incident not found")

        conn.execute(
            text("UPDATE incidents SET assigned_to = :assigned_to WHERE id = :id"),
            {"id": incident_id, "assigned_to": data.assigned_to},
        )

        if data.comment:
            conn.execute(
                text("""
                    INSERT INTO incident_comments (incident_id, author, content)
                    VALUES (:iid, :author, :content)
                """),
                {
                    "iid": incident_id,
                    "author": current_user.username,
                    "content": data.comment,
                },
            )

    log_audit(
        current_user.username, current_user.tenant_id, "assign", "incident",
        resource_id=str(incident_id),
        changes={"assigned_to": data.assigned_to},
    )

    # Sync to i-doit
    try:
        from core.idoit_service import push_assignment
        push_assignment(incident_id, data.assigned_to)
    except Exception as e:
        logger.warning(f"i-doit assign sync failed: {e}")

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()
    return _row_to_incident(row)


@router.post("/{incident_id}/escalate", response_model=IncidentRead)
def escalate_incident(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    """Manually escalate an incident to the next level."""
    engine = get_engine()
    now = datetime.now(timezone.utc)

    # Lock the incident row and run the read-check-write as one transaction so
    # the level increment and the comment insert cannot interleave or partially commit.
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT id, escalation_level, escalation_chain_id, status
                FROM incidents WHERE id = :id AND tenant_id = :tid FOR UPDATE
            """),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

        if not row:
            raise HTTPException(404, "Incident not found")
        if row["status"] in ("resolved", "closed"):
            raise HTTPException(400, "Cannot escalate resolved/closed incident")

        current_level = row["escalation_level"] or 0
        next_level_num = current_level + 1

        chain_id = row["escalation_chain_id"]
        if not chain_id:
            # Try to find default chain
            chain = conn.execute(
                text("SELECT id FROM escalation_chains WHERE tenant_id = :tid AND is_active = true ORDER BY created_at LIMIT 1"),
                {"tid": current_user.tenant_id},
            ).mappings().first()
            if not chain:
                raise HTTPException(400, "No escalation chain configured")
            chain_id = chain["id"]

        level_info = conn.execute(
            text("SELECT level, notify_role, notify_users FROM escalation_levels WHERE chain_id = :cid AND level = :lvl"),
            {"cid": chain_id, "lvl": next_level_num},
        ).mappings().first()

        if not level_info:
            raise HTTPException(400, f"No escalation level {next_level_num} defined in chain")

        conn.execute(
            text("""
                UPDATE incidents SET
                    escalation_level = :level,
                    escalation_chain_id = :chain_id,
                    status = 'escalated',
                    last_escalated_at = :now
                WHERE id = :id
            """),
            {"id": incident_id, "level": next_level_num, "chain_id": chain_id, "now": now},
        )

        conn.execute(
            text("""
                INSERT INTO incident_comments (incident_id, author, content)
                VALUES (:iid, :author, :content)
            """),
            {
                "iid": incident_id,
                "author": current_user.username,
                "content": f"Escalated to L{next_level_num} ({level_info['notify_role']})",
            },
        )

    log_audit(
        current_user.username, current_user.tenant_id, "escalate", "incident",
        resource_id=str(incident_id),
        changes={"from_level": current_level, "to_level": next_level_num},
    )

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

    # Notify the level's target (role + named users), same channel the auto-escalation uses.
    try:
        from core.notifications import notify
        users = level_info["notify_users"] or []
        target = level_info["notify_role"] + (f" ({', '.join(users)})" if users else "")
        notify(
            f"Эскалация L{next_level_num} → {target}: инцидент #{incident_id} "
            f"({row['metric']}/{row['region']})",
            "critical" if next_level_num >= 3 else "warning",
            event_type="escalation", tenant_id=current_user.tenant_id,
        )
    except Exception as e:
        logger.warning(f"Escalation notification failed: {e}")

    return _row_to_incident(row)


# --- Comments ---

@router.get("/{incident_id}/comments", response_model=List[IncidentCommentRead])
def list_comments(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

    if not exists:
        raise HTTPException(404, "Incident not found")

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, incident_id, author, content, created_at
                FROM incident_comments WHERE incident_id = :iid
                ORDER BY created_at ASC
            """),
            {"iid": incident_id},
        ).mappings().all()

    return [IncidentCommentRead(**r) for r in rows]


@router.post("/{incident_id}/comments", response_model=IncidentCommentRead, status_code=201)
def add_comment(
    incident_id: int,
    data: IncidentCommentCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

    if not exists:
        raise HTTPException(404, "Incident not found")

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                INSERT INTO incident_comments (incident_id, author, content)
                VALUES (:iid, :author, :content)
                RETURNING id, incident_id, author, content, created_at
            """),
            {"iid": incident_id, "author": current_user.username, "content": data.content},
        ).mappings().first()

    # Sync comment to i-doit
    try:
        from core.idoit_service import push_comment
        push_comment(incident_id, current_user.username, data.content)
    except Exception as e:
        logger.warning(f"i-doit comment sync failed: {e}")

    return IncidentCommentRead(**row)


# --- SLA Policies ---

@router.get("/sla/policies", response_model=List[SlaPolicyRead])
def list_sla_policies(
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, tenant_id, name, priority, response_time_minutes,
                       resolution_time_minutes, escalation_after_minutes, is_active, created_at
                FROM sla_policies WHERE tenant_id = :tid ORDER BY priority
            """),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [SlaPolicyRead(**r) for r in rows]


@router.post("/sla/policies", response_model=SlaPolicyRead, status_code=201)
def create_sla_policy(
    data: SlaPolicyCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO sla_policies (tenant_id, name, priority, response_time_minutes,
                                              resolution_time_minutes, escalation_after_minutes)
                    VALUES (:tid, :name, :priority, :resp, :res, :esc)
                    RETURNING id, tenant_id, name, priority, response_time_minutes,
                              resolution_time_minutes, escalation_after_minutes, is_active, created_at
                """),
                {
                    "tid": current_user.tenant_id,
                    "name": data.name,
                    "priority": data.priority,
                    "resp": data.response_time_minutes,
                    "res": data.resolution_time_minutes,
                    "esc": data.escalation_after_minutes,
                },
            ).mappings().first()
        log_audit(current_user.username, current_user.tenant_id, "create", "sla_policy", resource_id=str(row["id"]))
        return SlaPolicyRead(**row)
    except Exception as e:
        logger.error("create_sla_policy failed: %s", mask_secrets(str(e)))
        raise HTTPException(400, "Failed to create SLA policy (invalid data or duplicate)")


@router.put("/sla/policies/{policy_id}", response_model=SlaPolicyRead)
def update_sla_policy(
    policy_id: UUID,
    data: SlaPolicyCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    UPDATE sla_policies SET
                        name = :name, priority = :priority,
                        response_time_minutes = :resp, resolution_time_minutes = :res,
                        escalation_after_minutes = :esc
                    WHERE id = :id AND tenant_id = :tid
                    RETURNING id, tenant_id, name, priority, response_time_minutes,
                              resolution_time_minutes, escalation_after_minutes, is_active, created_at
                """),
                {"id": policy_id, "tid": current_user.tenant_id, "name": data.name,
                 "priority": data.priority, "resp": data.response_time_minutes,
                 "res": data.resolution_time_minutes, "esc": data.escalation_after_minutes},
            ).mappings().first()
    except Exception as e:
        logger.error("update_sla_policy failed: %s", mask_secrets(str(e)))
        raise HTTPException(400, "Failed to update SLA policy (invalid data or duplicate priority)")
    if not row:
        raise HTTPException(404, "SLA policy not found")
    log_audit(current_user.username, current_user.tenant_id, "update", "sla_policy", resource_id=str(policy_id))
    return SlaPolicyRead(**row)


@router.delete("/sla/policies/{policy_id}", status_code=204)
def delete_sla_policy(
    policy_id: UUID,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    with engine.begin() as conn:
        # Incidents store their deadlines directly, so dropping a policy only needs to
        # clear the FK reference — existing incidents keep their computed SLA.
        conn.execute(
            text("UPDATE incidents SET sla_policy_id = NULL WHERE sla_policy_id = :id AND tenant_id = :tid"),
            {"id": policy_id, "tid": current_user.tenant_id},
        )
        res = conn.execute(
            text("DELETE FROM sla_policies WHERE id = :id AND tenant_id = :tid"),
            {"id": policy_id, "tid": current_user.tenant_id},
        )
    if res.rowcount == 0:
        raise HTTPException(404, "SLA policy not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "sla_policy", resource_id=str(policy_id))
