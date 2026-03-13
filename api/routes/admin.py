# api/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import text
from core.database import get_engine
from core.rbac import require_role
from core.audit import log_audit
from api.auth import TokenData
from api.limiter import limiter
from config import mask_secrets

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Schemas ---

class TenantCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=1, max_length=200)


class TenantRead(BaseModel):
    id: str
    name: str
    is_active: bool


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    password: Optional[str] = None
    tenant_id: str = "default"


class UserRead(BaseModel):
    id: UUID
    username: str
    email: Optional[str]
    tenant_id: str
    is_active: bool
    auth_provider: str


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    tenant_id: str = "default"
    permissions: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class RoleRead(BaseModel):
    id: UUID
    name: str
    tenant_id: str
    permissions: list
    description: Optional[str]


class UserRoleAssign(BaseModel):
    user_id: UUID
    role_id: UUID


# --- Tenants ---

@router.get("/tenants", response_model=List[TenantRead], summary="List all tenants")
def list_tenants(current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, is_active FROM tenants ORDER BY id")).mappings().all()
        return [TenantRead(**row) for row in rows]


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED, summary="Create new tenant")
@limiter.limit("10/minute")
def create_tenant(request: Request, data: TenantCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
                {"id": data.id, "name": data.name},
            )
        log_audit(current_user.username, current_user.tenant_id, "create", "tenant", resource_id=data.id)
        return TenantRead(id=data.id, name=data.name, is_active=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- Users ---

@router.get("/users", response_model=List[UserRead], summary="List users in tenant")
def list_users(tenant_id: str = "default", current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, username, email, tenant_id, is_active, auth_provider FROM users WHERE tenant_id = :tid ORDER BY username"),
            {"tid": tenant_id},
        ).mappings().all()
        return [UserRead(**row) for row in rows]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create local user")
@limiter.limit("10/minute")
def create_user(request: Request, data: UserCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    password_hash = None
    if data.password:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(data.password)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, tenant_id)
                    VALUES (:username, :email, :password_hash, :tenant_id)
                    RETURNING id, username, email, tenant_id, is_active, auth_provider
                """),
                {
                    "username": data.username,
                    "email": data.email,
                    "password_hash": password_hash,
                    "tenant_id": data.tenant_id,
                },
            ).mappings().first()
            log_audit(current_user.username, current_user.tenant_id, "create", "user", resource_id=data.username)
            return UserRead(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- Roles ---

@router.get("/roles", response_model=List[RoleRead], summary="List roles in tenant")
def list_roles(tenant_id: str = "default", current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, tenant_id, permissions, description FROM roles WHERE tenant_id = :tid ORDER BY name"),
            {"tid": tenant_id},
        ).mappings().all()
        return [RoleRead(**row) for row in rows]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED, summary="Create role with permissions")
@limiter.limit("10/minute")
def create_role(request: Request, data: RoleCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    import json
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO roles (name, tenant_id, permissions, description)
                    VALUES (:name, :tenant_id, :permissions, :description)
                    RETURNING id, name, tenant_id, permissions, description
                """),
                {
                    "name": data.name,
                    "tenant_id": data.tenant_id,
                    "permissions": json.dumps(data.permissions),
                    "description": data.description,
                },
            ).mappings().first()
            log_audit(current_user.username, current_user.tenant_id, "create", "role", resource_id=data.name)
            return RoleRead(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- User-Role assignment ---

@router.post("/user-roles", status_code=status.HTTP_201_CREATED, summary="Assign role to user")
@limiter.limit("10/minute")
def assign_role(request: Request, data: UserRoleAssign, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid) ON CONFLICT DO NOTHING"),
                {"uid": data.user_id, "rid": data.role_id},
            )
        log_audit(current_user.username, current_user.tenant_id, "assign_role", "user_role",
                  resource_id=str(data.user_id), changes={"role_id": str(data.role_id)})
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


@router.delete("/user-roles", status_code=status.HTTP_204_NO_CONTENT, summary="Remove role from user")
def unassign_role(data: UserRoleAssign, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid AND role_id = :rid"),
            {"uid": data.user_id, "rid": data.role_id},
        )
    log_audit(current_user.username, current_user.tenant_id, "unassign_role", "user_role",
              resource_id=str(data.user_id), changes={"role_id": str(data.role_id)})
