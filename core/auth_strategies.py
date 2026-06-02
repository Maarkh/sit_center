# core/auth_strategies.py
"""Authentication strategies: LDAP, DB-based, env-based admin fallback."""
import json
from datetime import timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy import text as sa_text

from api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from core.passwords import verify_password
from config import logger, settings, mask_secrets


def _make_token(sub: str, tenant_id: str, roles: list, permissions: list) -> str:
    return create_access_token(
        data={
            "sub": sub,
            "scopes": ["admin"] if "admin" in roles else [],
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": list(set(permissions)),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def try_ldap_auth(username: str, password: str) -> Optional[str]:
    """Try LDAP authentication. Returns access_token or None."""
    if not getattr(settings, "LDAP_ENABLED", False):
        return None
    try:
        from core.ldap_auth import ldap_authenticator
        ldap_user = ldap_authenticator.authenticate(username, password)
        if not ldap_user:
            return None
        ldap_authenticator.sync_user_to_db(ldap_user)
        roles = ldap_authenticator.get_roles_for_groups(ldap_user.groups)
        all_perms: list = []
        from core.database import get_engine
        engine = get_engine()
        for role_name in roles:
            with engine.connect() as c:
                r = c.execute(
                    sa_text("SELECT permissions FROM roles WHERE name = :name AND tenant_id = 'default'"),
                    {"name": role_name},
                ).mappings().first()
                if r:
                    perms = r["permissions"]
                    all_perms.extend(json.loads(perms) if isinstance(perms, str) else perms)
        return _make_token(ldap_user.username, "default", roles, all_perms)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"LDAP auth failed, falling back: {e}")
        return None


def try_db_auth(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Try DB-based user authentication. Returns {token, username, tenant_id} or None."""
    try:
        from core.database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            user_row = conn.execute(
                sa_text("""
                    SELECT u.id, u.username, u.password_hash, u.tenant_id, u.is_active,
                           COALESCE(
                               json_agg(DISTINCT r.name) FILTER (WHERE r.name IS NOT NULL),
                               '[]'
                           ) AS roles,
                           COALESCE(
                               json_agg(DISTINCT perm) FILTER (WHERE perm IS NOT NULL),
                               '[]'
                           ) AS permissions
                    FROM users u
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    LEFT JOIN LATERAL jsonb_array_elements_text(r.permissions) AS perm ON true
                    WHERE u.username = :username AND u.is_active = true
                    GROUP BY u.id, u.username, u.password_hash, u.tenant_id, u.is_active
                """),
                {"username": username},
            ).mappings().first()

            if not user_row or not user_row["password_hash"]:
                # User genuinely not found in the DB → it's fine to fall through
                # to other strategies (e.g. env-admin) in the caller.
                return None
            if not verify_password(password, user_row["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            token = _make_token(
                user_row["username"],
                user_row["tenant_id"],
                user_row["roles"] or [],
                user_row["permissions"] or [],
            )
            return {"token": token, "username": user_row["username"], "tenant_id": user_row["tenant_id"]}
    except HTTPException:
        raise
    except Exception as e:
        # A DB/operational error is NOT the same as "user not found". Fail CLOSED:
        # returning None here would let the login flow fall through to the
        # env-admin fallback, granting full admin to anyone who knows the admin
        # credentials whenever the database is merely unreachable.
        logger.error(f"DB auth error (failing closed): {mask_secrets(str(e))}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")


def try_env_admin_auth(username: str, password: str) -> str:
    """Env-based admin fallback. Raises HTTPException on failure."""
    if username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _make_token(
        username,
        "default",
        ["admin"],
        [
            "read:metrics", "write:metrics", "read:rules", "write:rules",
            "read:alerts", "write:alerts", "read:ml", "write:ml",
            "admin:tenants", "admin:users", "read:audit",
        ],
    )
