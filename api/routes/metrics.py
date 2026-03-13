# api/routes/metrics.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from api.schemas import MetricCreate, MetricRead, MetricUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.post("/", response_model=MetricRead, status_code=status.HTTP_201_CREATED, summary="Create metric definition")
@limiter.limit("30/minute")
def create_metric(
    request: Request,
    data: MetricCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    try:
        metric_name = service.create_metric(data, tenant_id=current_user.tenant_id)  # type: ignore
        metric = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
        if not metric:
            raise HTTPException(status_code=500, detail="Metric created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "metric", resource_id=metric_name)
        return metric
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[MetricRead], summary="List all metric definitions")
def list_metrics(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    return service.list_metrics(active_only=active_only, tenant_id=current_user.tenant_id)


@router.get("/{metric_name}", response_model=MetricRead, summary="Get metric by name")
def get_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    metric = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.put("/{metric_name}", response_model=MetricRead, summary="Update metric definition")
@limiter.limit("30/minute")
def update_metric(
    request: Request,
    metric_name: str,
    data: MetricUpdate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    if data.metric_name != metric_name:
        raise HTTPException(status_code=400, detail="Cannot change metric_name on update")

    try:
        service.create_metric(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Metric updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "metric", resource_id=metric_name)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete metric definition")
@limiter.limit("10/minute")
def delete_metric(
    request: Request,
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM metadata_metrics WHERE metric_name = :name AND tenant_id = :tid"),
                {"name": metric_name, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Metric not found")
        service._invalidate_cache("metrics")
        log_audit(current_user.username, current_user.tenant_id, "delete", "metric", resource_id=metric_name)
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))
