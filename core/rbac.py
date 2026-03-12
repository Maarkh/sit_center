# core/rbac.py
from fastapi import Depends, HTTPException
from api.auth import get_current_user, TokenData


def require_permission(perm: str):
    """FastAPI dependency: require a specific permission in the JWT."""
    def _check(current_user: TokenData = Depends(get_current_user)):
        if "admin" in current_user.scopes:
            return current_user
        if perm not in current_user.permissions:
            raise HTTPException(403, f"Missing permission: {perm}")
        return current_user
    return _check


def require_role(role: str):
    """FastAPI dependency: require a specific role in the JWT."""
    def _check(current_user: TokenData = Depends(get_current_user)):
        if "admin" in current_user.scopes:
            return current_user
        if role not in current_user.roles:
            raise HTTPException(403, f"Missing role: {role}")
        return current_user
    return _check
