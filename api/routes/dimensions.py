# api/routes/dimensions.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import DimensionCreate, DimensionRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import get_current_user, TokenData
from config import mask_secrets

router = APIRouter(prefix="/dimensions", tags=["Dimensions"])


@router.get("/me")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=DimensionRead, status_code=status.HTTP_201_CREATED)
def create_dimension(
    data: DimensionCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        dim_key = service.create_dimension(data) # type: ignore
        dim = service.get_dimension(dim_key)
        if not dim:
            raise HTTPException(status_code=500, detail="Dimension created but not found")
        return dim
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[DimensionRead])
def list_dimensions(service: MetadataService = Depends(get_metadata_service)):
    return service.list_dimensions()


@router.get("/{dimension_key}", response_model=DimensionRead)
def get_dimension(
    dimension_key: str,
    service: MetadataService = Depends(get_metadata_service)
):
    dim = service.get_dimension(dimension_key)
    if not dim:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return dim