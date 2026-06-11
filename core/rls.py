# core/rls.py
"""Row-Level Security request context (FIX-10, defense-in-depth tenant isolation).

The DB policies (migration 029) restrict a row to `app.current_tenant` when that GUC
is set, and fail open (allow all) when it is not. This module is the application side:
it carries the current request's tenant in a ContextVar and pushes it onto every
pooled connection at checkout, so per-request web queries are DB-enforced to one
tenant — even a query that forgot its WHERE tenant_id can't leak across tenants.

Workers / the collector never set the ContextVar, so their legitimate cross-tenant
work runs fail-open. The GUC is reset on connection check-in so a pooled connection
never carries one request's tenant into the next.

⚠️ RLS only bites a NON-superuser, non-BYPASSRLS DB role (see migration 029 / docs).
"""
import contextvars
from sqlalchemy import event

from config import settings, logger

# None → no tenant context (fail-open). Set per request once auth resolves the tenant.
current_tenant: contextvars.ContextVar = contextvars.ContextVar("rls_current_tenant", default=None)


def set_request_tenant(tenant_id) -> None:
    """Bind the current request/task to a tenant for RLS. No-op for falsy values.

    Must be called from an HTTP MIDDLEWARE, not a dependency: a contextvar set inside
    a FastAPI sync dependency runs in a separate threadpool context and never reaches
    the sync endpoint's DB checkout (verified empirically). Middleware-set values do
    propagate. See the bind_rls_tenant middleware in api/main.py."""
    current_tenant.set(str(tenant_id) if tenant_id else None)


def warn_if_rls_bypassed(engine) -> None:
    """Log a LOUD warning if RLS is enabled but the app's DB role bypasses it
    (SUPERUSER / BYPASSRLS) — in which case migration 029's policies are a silent
    no-op and RLS_ENABLED=true is false assurance. Cheap one-shot check at startup."""
    if not getattr(settings, "RLS_ENABLED", True):
        return
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            bypass = conn.execute(text(
                "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
            )).scalar()
        if bypass:
            logger.warning(
                "⚠️ RLS_ENABLED=true but the app connects as a SUPERUSER/BYPASSRLS role — "
                "row-level security is BYPASSED (migration 029 is a no-op). Run the app as "
                "a NOSUPERUSER NOBYPASSRLS role for tenant isolation to take effect "
                "(see docs/operations.md §10)."
            )
    except Exception as e:
        logger.debug("RLS role check skipped: %s", e)


def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Push the current request's tenant onto the connection at checkout. Every
    checkout overwrites it (tenant or '' for fail-open), so no check-in reset is
    needed — a connection never carries a stale tenant into its next use.

    The SET runs in autocommit so it leaves NO open transaction behind: otherwise
    SQLAlchemy's own connection reset (set_session) fails with "cannot be used inside
    a transaction". pool_pre_ping leaves the connection clean here, so toggling
    autocommit is safe."""
    if dbapi_conn is None:  # can happen on an invalidated/reconnecting checkout
        return
    value = current_tenant.get() or ""
    try:
        prev_autocommit = dbapi_conn.autocommit
        if not prev_autocommit:
            dbapi_conn.autocommit = True
        cur = dbapi_conn.cursor()
        # set_config(name, value, is_local=false) = session-scoped; parameterised
        # (a bare SET can't bind a value).
        cur.execute("SELECT set_config('app.current_tenant', %s, false)", (value,))
        cur.close()
        if not prev_autocommit:
            dbapi_conn.autocommit = False
    except Exception as e:  # never break connection handling over RLS bookkeeping
        logger.warning("RLS GUC set failed: %s", e)


_installed = False


def install_rls(engine) -> None:
    """Attach the checkout GUC hook to the engine (idempotent).
    Gated by settings.RLS_ENABLED so it can be turned off without a redeploy."""
    global _installed
    if _installed or not getattr(settings, "RLS_ENABLED", True):
        return
    target = getattr(engine, "sync_engine", engine)
    event.listen(target, "checkout", _on_checkout)
    _installed = True
    logger.info("RLS request-context hooks installed (per-request tenant → app.current_tenant)")
