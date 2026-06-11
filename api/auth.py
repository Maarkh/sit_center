# api/auth.py
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
import jwt  # PyJWT (replaces the unmaintained python-jose; HS256, symmetric key)
from pydantic import BaseModel, Field

from config import settings

if not settings.secret_key:
    raise RuntimeError("SECRET_KEY is not set. Set SECRET_KEY in env or .env and restart the app.")

# Fail fast on weak / placeholder keys in real deployments. With a guessable
# SECRET_KEY an attacker can forge a JWT (tenant_id/roles/permissions are read
# straight from the token) and impersonate an admin of any tenant. Skipped under
# TESTING so the test suites can run with short fixed keys.
if os.getenv("TESTING", "").lower() not in ("1", "true"):
    _WEAK_SECRETS = {
        "change-me-to-random-secret",
        "changeme",
        "secret",
        "your-secret-key",
        "test-secret-key-for-ci",
    }
    if settings.secret_key in _WEAK_SECRETS or len(settings.secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY is weak or set to the example default. Generate a strong random key "
            '(e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`) '
            "and set SECRET_KEY before starting the app."
        )

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ACCESS_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"

# auto_error=False: don't 401 when the Authorization header is absent — we fall
# back to the httpOnly cookie (browser SPA) before deciding the request is anon.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def set_auth_cookies(response: Response, token: str) -> None:
    """Set the httpOnly auth cookie + a readable CSRF cookie (double-submit)."""
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    secure = getattr(settings, "COOKIE_SECURE", True)
    response.set_cookie(
        ACCESS_COOKIE_NAME, token,
        max_age=max_age, httponly=True, secure=secure, samesite="lax", path="/",
    )
    # Not httpOnly on purpose: the SPA reads it and echoes it as X-CSRF-Token.
    response.set_cookie(
        CSRF_COOKIE_NAME, secrets.token_urlsafe(32),
        max_age=max_age, httponly=False, secure=secure, samesite="lax", path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    tenant_id: str = "default"
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # type: ignore
        scopes = payload.get("scopes", [])
        tenant_id = payload.get("tenant_id", "default")
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])
        if username is None:
            raise jwt.InvalidTokenError("token has no 'sub' claim")
        return TokenData(
            username=username,
            scopes=scopes,
            tenant_id=tenant_id,
            roles=roles,
            permissions=permissions,
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Sentinel: the DB query ran and confirmed there is no active user with that username.
_USER_ABSENT = object()


def _resolve_user_grants(username: str):
    """Re-resolve a user's tenant/roles/permissions from the DB (the source of truth) so
    a leaked or forged token cannot grant more than the user's CURRENT grants. Returns:
      (tenant_id, roles, permissions) — an active DB user was found;
      _USER_ABSENT — the query ran but no active user has that username;
      None — DB error (caller falls back to the token claims, as before this change)."""
    from sqlalchemy import text as sa_text
    from core.database import get_engine
    from config import logger, mask_secrets
    try:
        with get_engine().connect() as conn:
            row = conn.execute(sa_text("""
                SELECT u.tenant_id, u.is_active,
                       COALESCE(jsonb_agg(DISTINCT r.name) FILTER (WHERE r.name IS NOT NULL), '[]'::jsonb) AS roles,
                       COALESCE(jsonb_agg(DISTINCT perm) FILTER (WHERE perm IS NOT NULL), '[]'::jsonb) AS permissions
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                LEFT JOIN LATERAL jsonb_array_elements_text(r.permissions) AS perm ON true
                WHERE u.username = :username
                GROUP BY u.tenant_id, u.is_active
            """), {"username": username}).mappings().first()
    except Exception as e:
        logger.warning("auth re-resolve DB error (falling back to token claims): %s", mask_secrets(str(e)))
        return None
    if not row or not row["is_active"]:
        return _USER_ABSENT
    return row["tenant_id"], list(row["roles"] or []), list(row["permissions"] or [])


def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> TokenData:
    # Prefer the Authorization header (programmatic clients / tests); fall back to
    # the httpOnly cookie set for the browser SPA.
    if not token:
        token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    td = verify_token(token)
    # Under TESTING (and the local demo) tokens are env-admin / minted fixtures with no
    # DB user — trust the claims. In production, re-resolve authz from the DB so the
    # token's tenant_id/roles/permissions can't outlive a revocation or be forged.
    if os.getenv("TESTING", "").lower() in ("1", "true"):
        return td
    grants = _resolve_user_grants(td.username)
    if grants is None:
        return td  # DB error → token claims (don't lock everyone out on a DB blip)
    if grants is _USER_ABSENT:
        # no active DB user → only the env-admin bootstrap account may proceed on claims
        if td.username == settings.ADMIN_USERNAME and settings.ENV_ADMIN_ENABLED:
            return td
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer valid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant_id, roles, permissions = grants
    return TokenData(
        username=td.username,
        scopes=["admin"] if "admin" in roles else [],
        tenant_id=tenant_id, roles=roles, permissions=permissions,
    )
