# api/dependencies.py
from core.metadata_service import metadata_service
from core.database import get_engine
from core.tenant import set_current_tenant
from api.auth import get_current_user, TokenData
from fastapi import Depends, HTTPException


def get_metadata_service():
    return metadata_service


def get_db_engine():
    return get_engine()


def require_scope(required_scope: str):
    def _check(current_user: TokenData = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return _check


def get_tenant_context(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Set tenant context from JWT and return the user."""
    set_current_tenant(current_user.tenant_id)
    return current_user
