# api/routes/data_sources.py
# Admin CRUD for the data-source registry (M1) + a "test" probe. Secret config
# fields (tokens/passwords) are masked on read and preserved on update when the
# client sends them back as "***" — same contract as notification channels.
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
from core.data_sources import SOURCE_TYPES, SECRET_KEYS, probe

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])
MASK = "***"


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("type")
    @classmethod
    def _type_ok(cls, v):
        if v not in SOURCE_TYPES:
            raise ValueError(f"type must be one of {SOURCE_TYPES}")
        return v


class SourceRead(BaseModel):
    id: UUID
    name: str
    type: str
    config: Dict[str, Any]
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


def _row(r) -> SourceRead:
    return SourceRead(id=r["id"], name=r["name"], type=r["type"],
                      config=_mask(r["config"] or {}), enabled=r["enabled"])


@router.get("", response_model=List[SourceRead])
def list_sources(current_user: TokenData = Depends(require_permission("read:metrics"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, type, config, enabled FROM data_sources "
                 "WHERE tenant_id = :tid ORDER BY created_at"),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [_row(r) for r in rows]


@router.post("", response_model=SourceRead, status_code=201)
def create_source(data: SourceCreate, current_user: TokenData = Depends(require_permission("write:metrics"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""INSERT INTO data_sources (tenant_id, name, type, config, enabled)
                        VALUES (:tid, :name, :type, :config, :enabled)
                        RETURNING id, name, type, config, enabled"""),
                {"tid": current_user.tenant_id, "name": data.name, "type": data.type,
                 "config": json.dumps(data.config), "enabled": data.enabled},
            ).mappings().first()
    except Exception as e:
        # most likely the UNIQUE(tenant_id, name) constraint
        logger.warning("create_source failed: %s", mask_secrets(str(e)))
        raise HTTPException(400, "Could not create source (duplicate name?)")
    log_audit(current_user.username, current_user.tenant_id, "create", "data_source", resource_id=str(row["id"]))
    return _row(row)


@router.put("/{source_id}", response_model=SourceRead)
def update_source(source_id: UUID, data: SourceCreate,
                  current_user: TokenData = Depends(require_permission("write:metrics"))):
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT config FROM data_sources WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
            {"id": source_id, "tid": current_user.tenant_id},
        ).mappings().first()
        if not existing:
            raise HTTPException(404, "Source not found")
        merged = _merge_secrets(data.config, existing["config"] or {})
        row = conn.execute(
            text("""UPDATE data_sources SET
                        name = :name, type = :type, config = :config,
                        enabled = :enabled, updated_at = NOW()
                    WHERE id = :id AND tenant_id = :tid
                    RETURNING id, name, type, config, enabled"""),
            {"id": source_id, "tid": current_user.tenant_id, "name": data.name, "type": data.type,
             "config": json.dumps(merged), "enabled": data.enabled},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "update", "data_source", resource_id=str(source_id))
    return _row(row)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: UUID, current_user: TokenData = Depends(require_permission("write:metrics"))):
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text("DELETE FROM data_sources WHERE id = :id AND tenant_id = :tid"),
            {"id": source_id, "tid": current_user.tenant_id},
        )
    if res.rowcount == 0:
        raise HTTPException(404, "Source not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "data_source", resource_id=str(source_id))


@router.post("/{source_id}/test")
def test_source(source_id: UUID, current_user: TokenData = Depends(require_permission("write:metrics"))):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT type, config FROM data_sources WHERE id = :id AND tenant_id = :tid"),
            {"id": source_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(404, "Source not found")
    result = probe(row["type"], row["config"] or {})
    if not result.get("ok"):
        result["error"] = mask_secrets(str(result.get("error", "")))
    return result
