# api/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import RuleCreate, RuleRead, RuleUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: RuleCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        rule_id = service.create_rule(data)  # type: ignore
        rule = _get_rule_by_id(service, rule_id)
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "rule", resource_id=str(rule_id))
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[RuleRead])
def list_rules(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rules = service.list_active_rules()
    if not active_only:
        rules = _list_all_rules(service)
    return rules


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rule = _get_rule_by_id(service, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        service.create_rule(data)  # type: ignore
        updated = _get_rule_by_id(service, rule_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Rule updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "rule", resource_id=str(rule_id))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_rules SET is_active = false WHERE id = :id"),
                {"id": rule_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found")
        service._invalidate_cache("rules")
        log_audit(current_user.username, current_user.tenant_id, "delete", "rule", resource_id=str(rule_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


def _get_rule_by_id(service: MetadataService, rule_id: UUID):
    """Fetch a single rule by ID directly from DB."""
    engine = service._get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules WHERE id = :id
            """),
            {"id": rule_id},
        ).mappings().first()
    if not row:
        return None
    from core.metadata_service import RuleDTO
    return RuleDTO(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        condition=service._deserialize_json(row["condition"]),
        labels=service._deserialize_json(row["labels"]),
        actions=service._deserialize_json(row["actions"]),
        is_active=row["is_active"],
    )


def _list_all_rules(service: MetadataService):
    """List all rules including inactive ones."""
    engine = service._get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules ORDER BY name
            """),
        ).mappings().all()
    from core.metadata_service import RuleDTO
    return [
        RuleDTO(
            id=r["id"], name=r["name"], description=r["description"],
            condition=service._deserialize_json(r["condition"]),
            labels=service._deserialize_json(r["labels"]),
            actions=service._deserialize_json(r["actions"]),
            is_active=r["is_active"],
        )
        for r in rows
    ]
