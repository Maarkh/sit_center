# api/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from uuid import UUID
from api.schemas import RuleCreate, RuleRead, RuleUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from sqlalchemy import text
from config import mask_secrets, logger

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED, summary="Create alerting rule")
@limiter.limit("30/minute")
def create_rule(
    request: Request,
    data: RuleCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        rule_id = service.create_rule(data, tenant_id=current_user.tenant_id)  # type: ignore
        rule = _get_rule_by_id(service, rule_id)
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "rule", resource_id=str(rule_id))
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error("metadata endpoint error: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not save (invalid data or duplicate)")


@router.get("/", response_model=List[RuleRead], summary="List alerting rules")
def list_rules(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rules = service.list_active_rules(tenant_id=current_user.tenant_id)
    if not active_only:
        rules = _list_all_rules(service, tenant_id=current_user.tenant_id)
    return rules


@router.get("/{rule_id}", response_model=RuleRead, summary="Get rule by ID")
def get_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rule = _get_rule_by_id(service, rule_id, tenant_id=current_user.tenant_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=RuleRead, summary="Update alerting rule")
@limiter.limit("30/minute")
def update_rule(
    request: Request,
    rule_id: UUID,
    data: RuleUpdate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        service.create_rule(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = _get_rule_by_id(service, rule_id, tenant_id=current_user.tenant_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Rule updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "rule", resource_id=str(rule_id))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("metadata endpoint error: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not save (invalid data or duplicate)")


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate alerting rule")
@limiter.limit("10/minute")
def delete_rule(
    request: Request,
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_rules SET is_active = false WHERE id = :id AND tenant_id = :tid"),
                {"id": rule_id, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found")
        service._invalidate_cache("rules")
        log_audit(current_user.username, current_user.tenant_id, "delete", "rule", resource_id=str(rule_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error("metadata endpoint error: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=500, detail="Internal server error")


def _get_rule_by_id(service: MetadataService, rule_id: UUID, tenant_id: str = "default"):
    """Fetch a single rule by ID directly from DB."""
    engine = service._get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active,
                       created_at, updated_at
                FROM metadata_rules WHERE id = :id AND tenant_id = :tid
            """),
            {"id": rule_id, "tid": tenant_id},
        ).mappings().first()
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "condition": service._deserialize_json(row["condition"]),
        "labels": service._deserialize_json(row["labels"]),
        "actions": service._deserialize_json(row["actions"]),
        "is_active": row["is_active"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _list_all_rules(service: MetadataService, tenant_id: str = "default"):
    """List all rules including inactive ones."""
    engine = service._get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules WHERE tenant_id = :tid ORDER BY name
            """),
            {"tid": tenant_id},
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
