# api/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)
