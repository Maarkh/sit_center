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
    ContextVars are per-task, so this never leaks across requests."""
    if tenant_id:
        current_tenant.set(str(tenant_id))


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
