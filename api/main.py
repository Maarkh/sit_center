# api/main.py
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import logger, setup_logging, settings

# Настройка логирования (важно: до импорта других модулей)
setup_logging()

from api.routes import metrics, dimensions, rules, ml_configs, alerts, data, webhooks, admin, incidents, forecasts
from api.routes import auth as auth_routes
from api.routes import audit as audit_routes
from api.auth import Token, OAuth2PasswordRequestForm
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


# CORS — origins from CORS_ORIGINS env var (comma-separated)
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-KEY", "Accept"],
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
app.include_router(incidents.router)
app.include_router(forecasts.router)
app.include_router(auth_routes.router)
app.include_router(audit_routes.router)

# WebSocket
from api.routes.websocket import router as ws_router
app.include_router(ws_router)

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    from core.auth_strategies import try_ldap_auth, try_db_auth, try_env_admin_auth
    from core.audit import log_audit
    ip = request.client.host if request.client else None

    # 1) LDAP
    token = try_ldap_auth(form_data.username, form_data.password)
    if token:
        log_audit(form_data.username, "default", "login", "session", ip_address=ip)
        return {"access_token": token, "token_type": "bearer"}

    # 2) DB user
    db_result = try_db_auth(form_data.username, form_data.password)
    if db_result:
        log_audit(db_result["username"], db_result["tenant_id"], "login", "session", ip_address=ip)
        return {"access_token": db_result["token"], "token_type": "bearer"}

    # 3) Env-based admin fallback
    token = try_env_admin_auth(form_data.username, form_data.password)
    log_audit(form_data.username, "default", "login", "session", ip_address=ip)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "situational-center-api"}

@app.get("/metric")
async def metric():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
    
