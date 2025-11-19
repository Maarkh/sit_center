# api/routes/ml_configs.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import MLConfigCreate, MLConfigRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/ml/configs", tags=["ML Configs"])

@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=MLConfigRead, status_code=status.HTTP_201_CREATED)
def create_ml_config(
    service: MetadataService = Depends(get_metadata_service),
    data: MLConfigCreate = Depends()
):
    try:
        config_id = service.create_ml_config(data) # type: ignore
        config = next((c for c in service.list_active_ml_configs() if c.id == config_id), None)
        if not config:
            raise HTTPException(status_code=500, detail="Config created but not found")
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[MLConfigRead])
def list_ml_configs(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service)
):
    return service.list_active_ml_configs() if active_only else service.list_all_ml_configs()


@router.get("/{config_id}", response_model=MLConfigRead)
def get_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    configs = service.list_active_ml_configs()
    config = next((c for c in configs if c.id == config_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="ML config not found")
    return config


@router.put("/{config_id}", response_model=MLConfigRead)
def update_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    data: MLConfigCreate = Depends()
):
    try:
        # Используем create_ml_config — он же делает UPSERT
        service.create_ml_config(data) # type: ignore
        updated = next((c for c in service.list_active_ml_configs() if c.id == config_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Config updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_ml_configs SET is_active = false WHERE id = :id"),
                {"id": config_id}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="ML config not found")
        service._invalidate_cache("ml_configs")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))