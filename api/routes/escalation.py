# api/routes/escalation.py
# CRUD for escalation chains and their levels (who to notify, after how long).
# A chain is an ordered list of levels; auto-escalation (core/sla_service) and manual
# escalation (api/routes/incidents) walk it and notify each level's role/users.
import json
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from config import logger, mask_secrets

router = APIRouter(prefix="/escalation", tags=["Escalation"])


class EscalationLevelIn(BaseModel):
    level: int = Field(..., ge=1, le=99)
    notify_role: str = Field(..., min_length=1, max_length=100)
    notify_users: List[str] = Field(default_factory=list)
    escalate_after_minutes: int = Field(..., gt=0)


class EscalationLevelRead(EscalationLevelIn):
    id: UUID


class EscalationChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    levels: List[EscalationLevelIn] = Field(default_factory=list)


class EscalationChainRead(BaseModel):
    id: UUID
    name: str
    is_active: bool
    levels: List[EscalationLevelRead]


def _load_chains(conn, tenant_id: str, chain_id: UUID | None = None) -> List[EscalationChainRead]:
    where = "tenant_id = :tid" + (" AND id = :cid" if chain_id else "")
    params = {"tid": tenant_id}
    if chain_id:
        params["cid"] = chain_id
    chains = conn.execute(
        text(f"SELECT id, name, is_active FROM escalation_chains WHERE {where} ORDER BY created_at"),
        params,
    ).mappings().all()
    out = []
    for c in chains:
        levels = conn.execute(
            text("""SELECT id, level, notify_role, notify_users, escalate_after_minutes
                    FROM escalation_levels WHERE chain_id = :cid ORDER BY level"""),
            {"cid": c["id"]},
        ).mappings().all()
        out.append(EscalationChainRead(
            id=c["id"], name=c["name"], is_active=c["is_active"],
            levels=[EscalationLevelRead(
                id=l["id"], level=l["level"], notify_role=l["notify_role"],
                notify_users=l["notify_users"] or [],
                escalate_after_minutes=l["escalate_after_minutes"],
            ) for l in levels],
        ))
    return out


def _insert_levels(conn, chain_id: UUID, levels: List[EscalationLevelIn]) -> None:
    for lv in levels:
        conn.execute(
            text("""INSERT INTO escalation_levels (chain_id, level, notify_role, notify_users, escalate_after_minutes)
                    VALUES (:cid, :level, :role, :users, :mins)"""),
            {"cid": chain_id, "level": lv.level, "role": lv.notify_role,
             "users": json.dumps(lv.notify_users), "mins": lv.escalate_after_minutes},
        )


@router.get("/chains", response_model=List[EscalationChainRead])
def list_chains(current_user: TokenData = Depends(require_permission("read:alerts"))):
    engine = get_engine()
    with engine.connect() as conn:
        return _load_chains(conn, current_user.tenant_id)


@router.post("/chains", response_model=EscalationChainRead, status_code=201)
def create_chain(data: EscalationChainCreate, current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            cid = conn.execute(
                text("INSERT INTO escalation_chains (tenant_id, name) VALUES (:tid, :name) RETURNING id"),
                {"tid": current_user.tenant_id, "name": data.name},
            ).scalar()
            _insert_levels(conn, cid, data.levels)
            chain = _load_chains(conn, current_user.tenant_id, cid)[0]
    except Exception as e:
        logger.error("create_chain failed: %s", mask_secrets(str(e)))
        raise HTTPException(400, "Failed to create chain (duplicate level?)")
    log_audit(current_user.username, current_user.tenant_id, "create", "escalation_chain", resource_id=str(cid))
    return chain


@router.put("/chains/{chain_id}", response_model=EscalationChainRead)
def update_chain(chain_id: UUID, data: EscalationChainCreate,
                 current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            updated = conn.execute(
                text("UPDATE escalation_chains SET name = :name WHERE id = :id AND tenant_id = :tid"),
                {"id": chain_id, "tid": current_user.tenant_id, "name": data.name},
            ).rowcount
            if not updated:
                raise HTTPException(404, "Chain not found")
            conn.execute(text("DELETE FROM escalation_levels WHERE chain_id = :cid"), {"cid": chain_id})
            _insert_levels(conn, chain_id, data.levels)
            chain = _load_chains(conn, current_user.tenant_id, chain_id)[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_chain failed: %s", mask_secrets(str(e)))
        raise HTTPException(400, "Failed to update chain (duplicate level?)")
    log_audit(current_user.username, current_user.tenant_id, "update", "escalation_chain", resource_id=str(chain_id))
    return chain


@router.delete("/chains/{chain_id}", status_code=204)
def delete_chain(chain_id: UUID, current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    with engine.begin() as conn:
        # Detach any incidents pointing at this chain so the FK doesn't block deletion.
        conn.execute(
            text("UPDATE incidents SET escalation_chain_id = NULL WHERE escalation_chain_id = :id AND tenant_id = :tid"),
            {"id": chain_id, "tid": current_user.tenant_id},
        )
        res = conn.execute(
            text("DELETE FROM escalation_chains WHERE id = :id AND tenant_id = :tid"),
            {"id": chain_id, "tid": current_user.tenant_id},
        )
    if res.rowcount == 0:
        raise HTTPException(404, "Chain not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "escalation_chain", resource_id=str(chain_id))
