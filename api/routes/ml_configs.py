# api/routes/ml_configs.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import MLConfigCreate, MLConfigRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/ml/configs", tags=["ML Configs"])


@router.post("/", response_model=MLConfigRead, status_code=status.HTTP_201_CREATED)
def create_ml_config(
    data: MLConfigCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    try:
        config_id = service.create_ml_config(data, tenant_id=current_user.tenant_id)  # type: ignore
        config = next((c for c in service.list_active_ml_configs(tenant_id=current_user.tenant_id) if c.id == config_id), None)
        if not config:
            raise HTTPException(status_code=500, detail="Config created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "ml_config", resource_id=str(config_id))
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[MLConfigRead])
def list_ml_configs(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:ml")),
):
    tid = current_user.tenant_id
    return service.list_active_ml_configs(tenant_id=tid) if active_only else service.list_all_ml_configs(tenant_id=tid)


@router.get("/{config_id}", response_model=MLConfigRead)
def get_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:ml")),
):
    configs = service.list_active_ml_configs(tenant_id=current_user.tenant_id)
    config = next((c for c in configs if c.id == config_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="ML config not found")
    return config


@router.put("/{config_id}", response_model=MLConfigRead)
def update_ml_config(
    config_id: UUID,
    data: MLConfigCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    try:
        service.create_ml_config(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = next((c for c in service.list_active_ml_configs(tenant_id=current_user.tenant_id) if c.id == config_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Config updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "ml_config", resource_id=str(config_id))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_ml_configs SET is_active = false WHERE id = :id AND tenant_id = :tid"),
                {"id": config_id, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="ML config not found")
        service._invalidate_cache("ml_configs")
        log_audit(current_user.username, current_user.tenant_id, "delete", "ml_config", resource_id=str(config_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))
