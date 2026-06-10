# api/routes/auth.py
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from datetime import timedelta
from functools import partial
from typing import Optional
from config import settings, logger
from api.auth import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    set_auth_cookies,
    clear_auth_cookies,
    TokenData,
)
from api.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


def _oidc_sync_user_and_perms(username: str, email: Optional[str], sub: str, roles: list,
                              tenant_id: str = "default") -> list:
    """Sync the OIDC user row and resolve its permissions, in the given tenant.

    Synchronous DB work — call via run_in_threadpool so the awaited OIDC callback
    never blocks the event loop.
    """
    import json
    from sqlalchemy import text
    from core.database import get_engine

    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, email, tenant_id, auth_provider, external_id, is_active)
                    VALUES (:username, :email, :tenant_id, 'oidc', :sub, true)
                    ON CONFLICT (username) DO UPDATE SET
                        email = EXCLUDED.email,
                        auth_provider = 'oidc',
                        external_id = EXCLUDED.external_id,
                        is_active = true,
                        updated_at = NOW()
                """),
                {"username": username, "email": email, "sub": sub, "tenant_id": tenant_id},
            )
    except Exception as e:
        logger.warning("Failed to sync OIDC user: %s", e)

    permissions: list = []
    try:
        with engine.connect() as conn:
            for role_name in roles:
                r = conn.execute(
                    text("SELECT permissions FROM roles WHERE name = :name AND tenant_id = :tenant_id"),
                    {"name": role_name, "tenant_id": tenant_id},
                ).mappings().first()
                if r:
                    perms = r["permissions"]
                    permissions.extend(json.loads(perms) if isinstance(perms, str) else perms)
    except Exception as e:
        logger.warning("Failed to resolve OIDC permissions: %s", e)
    return permissions


def _valid_tenant_or_default(candidate: str) -> str:
    """Return `candidate` if it is an active tenant, else 'default'."""
    from sqlalchemy import text
    from core.database import get_engine
    try:
        with get_engine().connect() as conn:
            ok = conn.execute(
                text("SELECT 1 FROM tenants WHERE id = :id AND is_active = true"),
                {"id": candidate},
            ).first()
        return candidate if ok else "default"
    except Exception:
        return "default"


@router.get("/me", summary="Current authenticated user (for the SPA)")
def auth_me(current_user: TokenData = Depends(get_current_user)):
    """Return the current user's identity for the UI. With httpOnly-cookie auth the
    SPA can't decode the JWT itself, so it rehydrates auth state from here."""
    return {
        "username": current_user.username,
        "scopes": current_user.scopes,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
        "tenant_id": current_user.tenant_id,
    }


@router.post("/logout", summary="Clear the auth cookies")
def auth_logout(response: Response):
    clear_auth_cookies(response)
    return {"status": "ok"}


@router.get("/login/oidc")
@limiter.limit("10/minute")
async def login_oidc(request: Request):
    """Redirect user to Keycloak for OIDC login."""
    if not getattr(settings, "OIDC_ENABLED", False):
        raise HTTPException(501, "OIDC not enabled")

    from core.oidc_auth import oauth
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    redirect_uri = f"{base_url}/auth/callback/oidc"
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@router.get("/callback/oidc")
@limiter.limit("10/minute")
async def callback_oidc(request: Request):
    """Handle OIDC callback from Keycloak, create JWT."""
    if not getattr(settings, "OIDC_ENABLED", False):
        raise HTTPException(501, "OIDC not enabled")

    from core.oidc_auth import oauth
    try:
        token = await oauth.keycloak.authorize_access_token(request)
    except Exception as e:
        logger.error("OIDC callback error: %s", e)
        raise HTTPException(401, "OIDC authentication failed")

    userinfo = token.get("userinfo", {})
    username = userinfo.get("preferred_username") or userinfo.get("sub")
    email = userinfo.get("email")

    if not username:
        raise HTTPException(401, "No username in OIDC token")

    # Map Keycloak roles -> local permissions. Keycloak realm roles live in the
    # ACCESS token claims, NOT in userinfo/id_token, and authlib does not expose
    # an "access_token_claims" key — so decode the access token to read them.
    # (Without this every SSO user silently collapsed to "viewer".) CPU-only.
    kc_roles: list = []
    try:
        from jose import jwt as _jwt
        access_jwt = token.get("access_token", "")
        if access_jwt:
            claims = _jwt.get_unverified_claims(access_jwt)
            kc_roles = (claims.get("realm_access", {}) or {}).get("roles", []) or []
    except Exception as e:
        logger.warning("Failed to decode OIDC access-token roles: %s", e)
    if not kc_roles:
        # Some providers surface realm_access via userinfo instead.
        kc_roles = (userinfo.get("realm_access", {}) or {}).get("roles", []) or []
    roles = kc_roles if kc_roles else ["viewer"]

    # Tenant from a configurable claim (validated against the tenants table), not a
    # hardcoded 'default'. Empty OIDC_TENANT_CLAIM → 'default'.
    tenant_id = "default"
    if settings.OIDC_TENANT_CLAIM:
        candidate = str(userinfo.get(settings.OIDC_TENANT_CLAIM) or "").strip()
        if candidate:
            tenant_id = await run_in_threadpool(_valid_tenant_or_default, candidate)

    # User sync + permission resolution are synchronous DB calls — run them off
    # the event loop so this awaited handler doesn't block the worker.
    permissions = await run_in_threadpool(
        _oidc_sync_user_and_perms, username, email, userinfo.get("sub", ""), roles, tenant_id
    )

    access_token = create_access_token(
        data={
            "sub": username,
            "scopes": ["admin"] if "admin" in roles else [],
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": list(set(permissions)),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Audit log for OIDC login (sync DB → off the event loop)
    try:
        from core.audit import log_audit
        ip = request.client.host if request.client else None
        await run_in_threadpool(
            partial(log_audit, username, tenant_id, "login", "session", ip_address=ip)
        )
    except Exception as e:
        logger.warning("Failed to log OIDC audit: %s", e)

    # Set the JWT as an httpOnly cookie and redirect to the SPA without exposing
    # the token in the URL at all (no query, no fragment). The SPA then reads its
    # identity from GET /auth/me.
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    redirect = RedirectResponse(f"{base_url}/")
    set_auth_cookies(redirect, access_token)
    return redirect
