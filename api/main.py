# api/main.py
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import logger, setup_logging, settings

# Настройка логирования (важно: до импорта других модулей)
setup_logging()

from api.routes import metrics, dimensions, rules, ml_configs, alerts, data, webhooks, admin
from api.routes import auth as auth_routes
from api.routes import audit as audit_routes
from api.auth import create_access_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES, OAuth2PasswordRequestForm
from datetime import timedelta
from core.exceptions import (
    situational_center_error_handler,
    sqlalchemy_error_handler,
    SituationalCenterError
)

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from api.middleware import PrometheusMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import DatabaseError as SQLADatabaseError
from api.limiter import limiter
from passlib.context import CryptContext

ALERTS_SENT = Counter("alerts_sent_total", "Total alerts sent", ["priority"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from api.routes.websocket import alert_stream_task
    logger.info("🚀 Запуск API-сервера...")

    # Configure OIDC if enabled
    try:
        from core.oidc_auth import configure_oidc
        configure_oidc()
    except Exception as e:
        logger.warning(f"OIDC configuration failed: {e}")

    asyncio.create_task(alert_stream_task())
    yield
    logger.info("🛑 Остановка API-сервера...")

app = FastAPI(
    title="Situational Center API",
    description="REST API для управления ситуационным центром",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
    openapi_url="/openapi.json"
)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(PrometheusMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore
app.add_exception_handler(SituationalCenterError, situational_center_error_handler) # type: ignore
app.add_exception_handler(SQLADatabaseError, sqlalchemy_error_handler) # type: ignore


# CORS (настрой под свой фронтенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8050",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Подключаем роутеры
app.include_router(metrics.router)
app.include_router(dimensions.router)
app.include_router(rules.router)
app.include_router(ml_configs.router)
app.include_router(alerts.router)
app.include_router(data.router)
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(auth_routes.router)
app.include_router(audit_routes.router)

# WebSocket
from api.routes.websocket import router as ws_router
app.include_router(ws_router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Try LDAP auth first if enabled
    if getattr(settings, "LDAP_ENABLED", False):
        try:
            from core.ldap_auth import ldap_authenticator
            ldap_user = ldap_authenticator.authenticate(form_data.username, form_data.password)
            if ldap_user:
                ldap_authenticator.sync_user_to_db(ldap_user)
                roles = ldap_authenticator.get_roles_for_groups(ldap_user.groups)
                all_perms = []
                for role_name in roles:
                    from core.database import get_engine as _ge
                    from sqlalchemy import text as _t
                    eng = _ge()
                    with eng.connect() as c:
                        r = c.execute(
                            _t("SELECT permissions FROM roles WHERE name = :name AND tenant_id = 'default'"),
                            {"name": role_name},
                        ).mappings().first()
                        if r:
                            import json
                            all_perms.extend(json.loads(r["permissions"]) if isinstance(r["permissions"], str) else r["permissions"])
                access_token = create_access_token(
                    data={
                        "sub": ldap_user.username,
                        "scopes": ["admin"] if "admin" in roles else [],
                        "tenant_id": "default",
                        "roles": roles,
                        "permissions": list(set(all_perms)),
                    },
                    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                )
                from core.audit import log_audit
                log_audit(ldap_user.username, "default", "login", "session", ip_address=request.client.host if request.client else None)
                return {"access_token": access_token, "token_type": "bearer"}
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"LDAP auth failed, falling back: {e}")

    # Try DB-based user first
    try:
        from core.database import get_engine
        from sqlalchemy import text as sa_text
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
                {"username": form_data.username},
            ).mappings().first()

            if user_row and user_row["password_hash"]:
                if not pwd_context.verify(form_data.password, user_row["password_hash"]):
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                access_token = create_access_token(
                    data={
                        "sub": user_row["username"],
                        "scopes": ["admin"] if "admin" in (user_row["roles"] or []) else [],
                        "tenant_id": user_row["tenant_id"],
                        "roles": user_row["roles"] or [],
                        "permissions": user_row["permissions"] or [],
                    },
                    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                )
                from core.audit import log_audit
                log_audit(user_row["username"], user_row["tenant_id"], "login", "session", ip_address=request.client.host if request.client else None)
                return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception:
        pass  # Fallback to env-based admin

    # Env-based admin fallback
    if form_data.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(form_data.password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={
            "sub": form_data.username,
            "scopes": ["admin"],
            "tenant_id": "default",
            "roles": ["admin"],
            "permissions": ["read:metrics", "write:metrics", "read:rules", "write:rules",
                           "read:alerts", "write:alerts", "read:ml", "write:ml",
                           "admin:tenants", "admin:users", "read:audit"],
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    from core.audit import log_audit
    log_audit(form_data.username, "default", "login", "session", ip_address=request.client.host if request.client else None)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "situational-center-api"}

@app.get("/metric")
async def metric():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
    
