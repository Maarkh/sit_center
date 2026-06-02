# api/routes/dimensions.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from api.schemas import DimensionCreate, DimensionRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets, logger

router = APIRouter(prefix="/dimensions", tags=["Dimensions"])


@router.post("/", response_model=DimensionRead, status_code=status.HTTP_201_CREATED, summary="Create dimension definition")
@limiter.limit("30/minute")
def create_dimension(
    request: Request,
    data: DimensionCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    try:
        dim_key = service.create_dimension(data, tenant_id=current_user.tenant_id)  # type: ignore
        dim = service.get_dimension(dim_key, tenant_id=current_user.tenant_id)
        if not dim:
            raise HTTPException(status_code=500, detail="Dimension created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "dimension", resource_id=dim_key)
        return dim
    except HTTPException:
        raise
    except Exception as e:
        logger.error("metadata endpoint error: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not save (invalid data or duplicate)")


@router.get("/", response_model=List[DimensionRead], summary="List dimension definitions")
def list_dimensions(
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    return service.list_dimensions(tenant_id=current_user.tenant_id)


@router.get("/{dimension_key}", response_model=DimensionRead, summary="Get dimension by key")
def get_dimension(
    dimension_key: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    dim = service.get_dimension(dimension_key, tenant_id=current_user.tenant_id)
    if not dim:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return dim
