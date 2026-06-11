# api/main.py
import json
import secrets
from fastapi import FastAPI, Depends, Response, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from config import logger, setup_logging, settings

# Настройка логирования (важно: до импорта других модулей)
setup_logging()

from api.routes import metrics, dimensions, rules, ml_configs, alerts, data, webhooks, admin, incidents, forecasts
from api.routes import auth as auth_routes
from api.routes import audit as audit_routes
from api.routes import indicators as indicators_routes
from api.routes import deviations as deviations_routes
from api.routes import processes as processes_routes
from api.routes import recommendations as recommendations_routes
from api.routes import predictions as predictions_routes
from api.routes import situations as situations_routes
from api.routes import scenarios as scenarios_routes
from api.routes import escalation as escalation_routes
from api.routes import notifications as notifications_routes
from api.routes import data_sources as data_sources_routes
from api.routes import ingestion as ingestion_routes
from api.auth import Token, set_auth_cookies
from fastapi.security import OAuth2PasswordRequestForm
from core.exceptions import (
    situational_center_error_handler,
    sqlalchemy_error_handler,
    SituationalCenterError
)

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from api.middleware import PrometheusMiddleware, DeprecationMiddleware
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

    # Configure OpenTelemetry tracing if enabled
    try:
        from core.tracing import setup_tracing
        setup_tracing(app)
    except Exception as e:
        logger.warning(f"OpenTelemetry setup failed: {e}")

    # Start incident buffer processor (moved from module-level import)
    from core.alerts import start_incident_buffer_processor
    start_incident_buffer_processor()

    asyncio.create_task(alert_stream_task())
    yield
    logger.info("🛑 Остановка API-сервера...")

app = FastAPI(
    title="Situational Center API",
    description=(
        "Enterprise monitoring and incident management platform.\n\n"
        "Supports multi-tenancy, RBAC, LDAP/OIDC authentication, "
        "PromQL-like alerting rules, ML anomaly detection, "
        "and bidirectional i-doit ITSM integration.\n\n"
        "**Authentication**: `POST /token` with form fields `username` + `password`. "
        "Use the returned `access_token` as `Bearer` token in the `Authorization` header.\n\n"
        "**Rate limits**: Global 100 req/min per IP. Write operations have tighter limits."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "System", "description": "Health checks and Prometheus metrics"},
        {"name": "Metrics", "description": "CRUD for metric definitions (metadata)"},
        {"name": "Dimensions", "description": "CRUD for dimension definitions"},
        {"name": "Rules", "description": "Alerting rule management (PromQL-like conditions)"},
        {"name": "ML Configs", "description": "Machine learning model configurations"},
        {"name": "Alerts", "description": "Alert events: list, acknowledge, resolve, suppress"},
        {"name": "Data", "description": "Time-series data ingestion and query"},
        {"name": "Incidents", "description": "Incident lifecycle management with SLA tracking"},
        {"name": "Forecasts", "description": "ML-powered metric forecasting (Prophet)"},
        {"name": "Webhooks", "description": "Inbound webhooks from Grafana and i-doit"},
        {"name": "Admin", "description": "Tenant, user, and role management (admin only)"},
        {"name": "Auth", "description": "OIDC/Keycloak SSO login flow"},
        {"name": "Audit", "description": "Audit log queries"},
    ],
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(DeprecationMiddleware)
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
    allow_headers=["Authorization", "Content-Type", "X-API-KEY", "Accept", "X-CSRF-Token"],
)


# --- RLS request-tenant binding ---
# Bind each request to its tenant so DB Row-Level Security (migration 029) actually
# enforces isolation. This MUST be middleware: a contextvar set in a FastAPI sync
# dependency runs in a separate threadpool context and never reaches the sync
# endpoint's DB checkout — only a middleware-set value propagates (verified). The
# decode is best-effort and never rejects (auth is the route's job); an
# unauthenticated request gets no tenant → RLS fails open.
@app.middleware("http")
async def bind_rls_tenant(request: Request, call_next):
    from core.rls import current_tenant, set_request_tenant
    from api.auth import verify_token, ACCESS_COOKIE_NAME
    current_tenant.set(None)
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.cookies.get(ACCESS_COOKIE_NAME)
    if token:
        try:
            set_request_tenant(verify_token(token).tenant_id)
        except Exception:
            pass  # invalid/expired token → no tenant; the route's auth dep will 401
    return await call_next(request)


# --- CSRF protection for cookie-authenticated browser requests ---
# Double-submit token: an unsafe request that authenticates via the httpOnly
# cookie (i.e. has the access_token cookie and NO Authorization header) must echo
# the readable csrf_token cookie back in the X-CSRF-Token header. Programmatic
# Bearer clients (and tests) send the Authorization header and are exempt, since
# they aren't subject to CSRF (credentials aren't auto-attached by the browser).
_CSRF_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# /token: login carries no auth cookie yet. /auth/logout: only clears cookies
# (logout-CSRF is low risk) and must work even without a csrf cookie present.
_CSRF_EXEMPT_PATHS = {"/token", "/auth/logout"}


@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    if (
        request.method in _CSRF_UNSAFE_METHODS
        and request.url.path not in _CSRF_EXEMPT_PATHS
        and request.cookies.get("access_token")
        and not request.headers.get("authorization")
    ):
        cookie_csrf = request.cookies.get("csrf_token")
        header_csrf = request.headers.get("x-csrf-token")
        if not cookie_csrf or not header_csrf or not secrets.compare_digest(cookie_csrf, header_csrf):
            return JSONResponse(status_code=403, content={"detail": "CSRF token missing or invalid"})
    return await call_next(request)


# Security response headers. CSP is restrictive for the API (JSON) but skipped for the
# interactive docs (Swagger/ReDoc need inline scripts/styles + their CDN).
_CSP = "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    # HSTS is honoured only over HTTPS; harmless over plain HTTP.
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if not request.url.path.startswith(_DOCS_PREFIXES):
        response.headers.setdefault("Content-Security-Policy", _CSP)
    return response


# API v1 — all business routes under /api/v1/ prefix
API_V1_PREFIX = "/api/v1"
app.include_router(metrics.router, prefix=API_V1_PREFIX)
app.include_router(dimensions.router, prefix=API_V1_PREFIX)
app.include_router(rules.router, prefix=API_V1_PREFIX)
app.include_router(ml_configs.router, prefix=API_V1_PREFIX)
app.include_router(alerts.router, prefix=API_V1_PREFIX)
app.include_router(data.router, prefix=API_V1_PREFIX)
app.include_router(webhooks.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(incidents.router, prefix=API_V1_PREFIX)
app.include_router(forecasts.router, prefix=API_V1_PREFIX)
app.include_router(auth_routes.router, prefix=API_V1_PREFIX)
app.include_router(audit_routes.router, prefix=API_V1_PREFIX)
# DSS modules (M2 Indicator&Goal, M3 Deviation, M8 Process)
app.include_router(indicators_routes.router, prefix=API_V1_PREFIX)
app.include_router(deviations_routes.router, prefix=API_V1_PREFIX)
app.include_router(processes_routes.router, prefix=API_V1_PREFIX)
app.include_router(recommendations_routes.playbooks_router, prefix=API_V1_PREFIX)
app.include_router(recommendations_routes.recommendations_router, prefix=API_V1_PREFIX)
app.include_router(predictions_routes.router, prefix=API_V1_PREFIX)
app.include_router(situations_routes.router, prefix=API_V1_PREFIX)
app.include_router(scenarios_routes.router, prefix=API_V1_PREFIX)
app.include_router(escalation_routes.router, prefix=API_V1_PREFIX)
app.include_router(notifications_routes.router, prefix=API_V1_PREFIX)
app.include_router(data_sources_routes.router, prefix=API_V1_PREFIX)
app.include_router(ingestion_routes.router, prefix=API_V1_PREFIX)
app.include_router(ingestion_routes.router)

# Backward-compat: also mount without prefix for existing clients
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

@app.post("/token", response_model=Token, tags=["System"], summary="Authenticate and get JWT token")
@limiter.limit("5/minute")
def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    from core.auth_strategies import try_ldap_auth, try_db_auth, try_env_admin_auth
    from core.audit import log_audit
    ip = request.client.host if request.client else None

    # The JWT is set as an httpOnly cookie (browser SPA) AND returned in the body
    # (programmatic clients / OIDC / tests). The browser path ignores the body.

    # 1) LDAP
    token = try_ldap_auth(form_data.username, form_data.password)
    if token:
        log_audit(form_data.username, "default", "login", "session", ip_address=ip)
        set_auth_cookies(response, token)
        return {"access_token": token, "token_type": "bearer"}

    # 2) DB user
    db_result = try_db_auth(form_data.username, form_data.password)
    if db_result:
        log_audit(db_result["username"], db_result["tenant_id"], "login", "session", ip_address=ip)
        set_auth_cookies(response, db_result["token"])
        return {"access_token": db_result["token"], "token_type": "bearer"}

    # 3) Env-based admin fallback (bootstrap only; disable in prod via ENV_ADMIN_ENABLED=false)
    if not settings.ENV_ADMIN_ENABLED:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = try_env_admin_auth(form_data.username, form_data.password)
    log_audit(form_data.username, "default", "login", "session", ip_address=ip)
    set_auth_cookies(response, token)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/v1/frontend-errors")
async def frontend_errors(request: Request):
    """Collect frontend error reports for monitoring."""
    try:
        body = await request.json()
        logger.warning(
            "Frontend error: %s | url=%s | stack=%s",
            body.get("message", "unknown"),
            body.get("url", ""),
            (body.get("stack", "") or "")[:500],
        )
    except Exception:
        pass
    return {"status": "ok"}


@app.get("/health", tags=["System"])
def health():
    """Aggregated health check for all dependencies."""
    import time
    checks = {}

    # Database
    try:
        from core.database import get_engine
        engine = get_engine()
        start = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:200]}

    # Redis
    try:
        from config import get_redis
        start = time.perf_counter()
        get_redis().ping()
        checks["redis"] = {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
    except Exception as e:
        checks["redis"] = {"status": "error", "detail": str(e)[:200]}

    # Kafka (optional)
    if settings.KAFKA_ENABLED:
        try:
            from kafka import KafkaProducer
            start = time.perf_counter()
            p = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, request_timeout_ms=3000)
            p.close(timeout=2)
            checks["kafka"] = {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            checks["kafka"] = {"status": "error", "detail": str(e)[:200]}

    # ClickHouse (optional)
    if settings.CLICKHOUSE_ENABLED:
        try:
            import clickhouse_connect
            start = time.perf_counter()
            ch = clickhouse_connect.get_client(
                host=settings.CLICKHOUSE_HOST, port=settings.CLICKHOUSE_PORT,
                username=settings.CLICKHOUSE_USER, password=settings.CLICKHOUSE_PASSWORD,
            )
            ch.ping()
            ch.close()
            checks["clickhouse"] = {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            checks["clickhouse"] = {"status": "error", "detail": str(e)[:200]}

    overall = "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded"
    status_code = 200 if overall == "ok" else 503
    return Response(
        content=json.dumps({"status": overall, "service": "situational-center-api", "checks": checks}),
        media_type="application/json",
        status_code=status_code,
    )

@app.get("/metric", tags=["System"], summary="Prometheus metrics endpoint")
def metric():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    # Dev-only entrypoint (reload=True). Production runs via the container CMD with
    # the bind address controlled by the deployment, not this 0.0.0.0 default.
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
    
