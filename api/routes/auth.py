# api/routes/auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from datetime import timedelta
from config import settings, logger
from api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login/oidc")
async def login_oidc(request: Request):
    """Redirect user to Keycloak for OIDC login."""
    if not getattr(settings, "OIDC_ENABLED", False):
        raise HTTPException(501, "OIDC not enabled")

    from core.oidc_auth import oauth
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    redirect_uri = f"{base_url}/auth/callback/oidc"
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@router.get("/callback/oidc")
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

    # Sync user to DB
    try:
        from sqlalchemy import text
        from core.database import get_engine
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, email, tenant_id, auth_provider, external_id, is_active)
                    VALUES (:username, :email, 'default', 'oidc', :sub, true)
                    ON CONFLICT (username) DO UPDATE SET
                        email = EXCLUDED.email,
                        auth_provider = 'oidc',
                        external_id = EXCLUDED.external_id,
                        is_active = true,
                        updated_at = NOW()
                """),
                {"username": username, "email": email, "sub": userinfo.get("sub", "")},
            )
    except Exception as e:
        logger.warning("Failed to sync OIDC user: %s", e)

    # Map Keycloak roles -> local permissions
    realm_access = token.get("access_token_claims", {}).get("realm_access", {})
    kc_roles = realm_access.get("roles", [])
    roles = kc_roles if kc_roles else ["viewer"]

    # Resolve permissions from DB roles
    permissions: list = []
    try:
        from sqlalchemy import text as _t
        with engine.connect() as conn:
            for role_name in roles:
                r = conn.execute(
                    _t("SELECT permissions FROM roles WHERE name = :name AND tenant_id = 'default'"),
                    {"name": role_name},
                ).mappings().first()
                if r:
                    import json as _json
                    perms = r["permissions"]
                    permissions.extend(_json.loads(perms) if isinstance(perms, str) else perms)
    except Exception as e:
        logger.warning("Failed to resolve OIDC permissions: %s", e)

    access_token = create_access_token(
        data={
            "sub": username,
            "scopes": ["admin"] if "admin" in roles else [],
            "tenant_id": "default",
            "roles": roles,
            "permissions": list(set(permissions)),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Audit log for OIDC login
    try:
        from core.audit import log_audit
        ip = request.client.host if request.client else None
        log_audit(username, "default", "login", "session", ip_address=ip)
    except Exception as e:
        logger.warning("Failed to log OIDC audit: %s", e)

    # Redirect to frontend with token
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    return RedirectResponse(f"{base_url}/?token={access_token}")
