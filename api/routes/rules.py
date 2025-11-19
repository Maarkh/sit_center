# api/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import RuleCreate, RuleRead, RuleUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: RuleCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        rule_id = service.create_rule(data) # type: ignore
        # Перечитываем для full-объекта
        rules = service.list_active_rules() + [r for r in [] if not r.is_active]  # TODO: сделать get_rule(id)
        rule = next((r for r in rules if r.id == rule_id), None)
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        return rule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[RuleRead])
def list_rules(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service)
):
    if active_only:
        return service.list_active_rules()
    else:
        # TODO: добавить list_all_rules()
        return service.list_active_rules()


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    rules = service.list_active_rules()
    rule = next((r for r in rules if r.id == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    service: MetadataService = Depends(get_metadata_service)
):
    # Создаём DTO с id
    from dataclasses import replace
    dto = data
    # В create_rule поддерживается id
    try:
        service.create_rule(dto) # type: ignore
        updated = next((r for r in service.list_active_rules() if r.id == rule_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Rule updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_rules SET is_active = false WHERE id = :id"),
                {"id": rule_id}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found")
        service._invalidate_cache("rules")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))