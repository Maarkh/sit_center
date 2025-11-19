# api/routes/metrics.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import MetricCreate, MetricRead, MetricUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.post("/", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
def create_metric(
    data: MetricCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        metric_name = service.create_metric(data) # type: ignore
        metric = service.get_metric(metric_name)
        if not metric:
            raise HTTPException(status_code=500, detail="Metric created but not found")
        return metric
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[MetricRead])
def list_metrics(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(get_current_user) 
):
    return service.list_metrics(active_only=active_only)


@router.get("/{metric_name}", response_model=MetricRead)
def get_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service)
):
    metric = service.get_metric(metric_name)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.put("/{metric_name}", response_model=MetricRead)
def update_metric(
    metric_name: str,
    data: MetricUpdate,
    service: MetadataService = Depends(get_metadata_service)
):
    # Валидация: нельзя изменить имя
    if data.metric_name != metric_name:
        raise HTTPException(status_code=400, detail="Cannot change metric_name on update")
    
    try:
        # Просто вызываем create — он делает ON CONFLICT DO UPDATE
        service.create_metric(data) # type: ignore
        updated = service.get_metric(metric_name)
        if not updated:
            raise HTTPException(status_code=500, detail="Metric updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service)
):
    # В PostgreSQL — удаляем вручную (metadata_metrics не имеет каскада)
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM metadata_metrics WHERE metric_name = :name"),
                {"name": metric_name}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Metric not found")
        service._invalidate_cache("metrics")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))