# api/routes/notifications.py
# Admin CRUD for notification channels + a "send test" action. Secret config fields
# (tokens/passwords) are masked on read and preserved on update when sent back as "***".
import json
from uuid import UUID
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from config import logger, mask_secrets
from core.notification_channels import (
    CHANNEL_TYPES, EVENT_TYPES, PRIORITIES, SECRET_KEYS, send_to_channel,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])
MASK = "***"


class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    event_types: List[str] = Field(default_factory=list)
    min_priority: str = "info"
    enabled: bool = True

    @field_validator("type")
    @classmethod
    def _type_ok(cls, v):
        if v not in CHANNEL_TYPES:
            raise ValueError(f"type must be one of {CHANNEL_TYPES}")
        return v

    @field_validator("event_types")
    @classmethod
    def _events_ok(cls, v):
        allowed = set(EVENT_TYPES) | {"all"}
        bad = [e for e in v if e not in allowed]
        if bad:
            raise ValueError(f"unknown event types {bad}; allowed {sorted(allowed)}")
        return v

    @field_validator("min_priority")
    @classmethod
    def _prio_ok(cls, v):
        if v not in PRIORITIES:
            raise ValueError(f"min_priority must be one of {PRIORITIES}")
        return v


class ChannelRead(BaseModel):
    id: UUID
    name: str
    type: str
    config: Dict[str, Any]
    event_types: List[str]
    min_priority: str
    enabled: bool


def _mask(config: dict) -> dict:
    out = dict(config or {})
    for k in SECRET_KEYS:
        if out.get(k):
            out[k] = MASK
    return out


def _merge_secrets(incoming: dict, existing: dict) -> dict:
    """Keep the stored secret when the client sends back the masked sentinel."""
    out = dict(incoming or {})
    for k in SECRET_KEYS:
        if out.get(k) == MASK:
            out[k] = (existing or {}).get(k, "")
    return out


def _row(r) -> ChannelRead:
    return ChannelRead(
        id=r["id"], name=r["name"], type=r["type"], config=_mask(r["config"] or {}),
        event_types=r["event_types"] or [], min_priority=r["min_priority"], enabled=r["enabled"],
    )


@router.get("/channels", response_model=List[ChannelRead])
def list_channels(current_user: TokenData = Depends(require_permission("read:alerts"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, type, config, event_types, min_priority, enabled "
                 "FROM notification_channels WHERE tenant_id = :tid ORDER BY created_at"),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [_row(r) for r in rows]


@router.post("/channels", response_model=ChannelRead, status_code=201)
def create_channel(data: ChannelCreate, current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("""INSERT INTO notification_channels (tenant_id, name, type, config, event_types, min_priority, enabled)
                    VALUES (:tid, :name, :type, :config, :events, :prio, :enabled)
                    RETURNING id, name, type, config, event_types, min_priority, enabled"""),
            {"tid": current_user.tenant_id, "name": data.name, "type": data.type,
             "config": json.dumps(data.config), "events": json.dumps(data.event_types),
             "prio": data.min_priority, "enabled": data.enabled},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "create", "notification_channel", resource_id=str(row["id"]))
    return _row(row)


@router.put("/channels/{channel_id}", response_model=ChannelRead)
def update_channel(channel_id: UUID, data: ChannelCreate,
                   current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT config FROM notification_channels WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
            {"id": channel_id, "tid": current_user.tenant_id},
        ).mappings().first()
        if not existing:
            raise HTTPException(404, "Channel not found")
        merged = _merge_secrets(data.config, existing["config"] or {})
        row = conn.execute(
            text("""UPDATE notification_channels SET
                        name = :name, type = :type, config = :config, event_types = :events,
                        min_priority = :prio, enabled = :enabled, updated_at = NOW()
                    WHERE id = :id AND tenant_id = :tid
                    RETURNING id, name, type, config, event_types, min_priority, enabled"""),
            {"id": channel_id, "tid": current_user.tenant_id, "name": data.name, "type": data.type,
             "config": json.dumps(merged), "events": json.dumps(data.event_types),
             "prio": data.min_priority, "enabled": data.enabled},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "update", "notification_channel", resource_id=str(channel_id))
    return _row(row)


@router.delete("/channels/{channel_id}", status_code=204)
def delete_channel(channel_id: UUID, current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text("DELETE FROM notification_channels WHERE id = :id AND tenant_id = :tid"),
            {"id": channel_id, "tid": current_user.tenant_id},
        )
    if res.rowcount == 0:
        raise HTTPException(404, "Channel not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "notification_channel", resource_id=str(channel_id))


@router.post("/channels/{channel_id}/test")
def test_channel(channel_id: UUID, current_user: TokenData = Depends(require_permission("write:alerts"))):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT type, config FROM notification_channels WHERE id = :id AND tenant_id = :tid"),
            {"id": channel_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(404, "Channel not found")
    try:
        send_to_channel(row["type"], row["config"] or {}, "✅ Тест уведомления из Ситуационного центра",
                        "info", "system")
        return {"ok": True}
    except Exception as e:
        logger.warning("test_channel failed: %s", mask_secrets(str(e)))
        return {"ok": False, "error": mask_secrets(str(e))}
