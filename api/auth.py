# api/auth.py
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
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
            raise JWTError()
        return TokenData(
            username=username,
            scopes=scopes,
            tenant_id=tenant_id,
            roles=roles,
            permissions=permissions,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
    return verify_token(token)
