# tests/integration/test_rls.py
"""Integration test for DB-level Row-Level Security (FIX-10, migration 029).

The CI/demo DB role is a superuser (which BYPASSES RLS), so we prove enforcement
the same way the app role would experience it in production: SET ROLE to a throwaway
NON-superuser role, then check that `app.current_tenant` filters rows. Everything runs
in one transaction that is rolled back, so neither the role nor the seed data persists.
"""
import pytest
from sqlalchemy import text


def test_rls_enforces_tenant_isolation(db_engine):
    with db_engine.connect() as probe:
        has_policy = probe.execute(text(
            "SELECT 1 FROM pg_policies WHERE tablename='deviations' "
            "AND policyname='tenant_isolation'"
        )).first()
    if not has_policy:
        pytest.skip("RLS migration 029 not applied")

    iid = "11111111-1111-1111-1111-111111111111"
    conn = db_engine.connect()
    trans = conn.begin()
    try:
        conn.execute(text(
            "INSERT INTO indicators (id,tenant_id,name,direction,chronicle_threshold,"
            "corridor_type,is_active) VALUES (:i,'default','__rls_it__','both',3,'static',true)"),
            {"i": iid})
        conn.execute(text(
            "INSERT INTO deviations (tenant_id,indicator_id,direction,value,severity,status,"
            "periods,fingerprint) VALUES ('default',:i,'above',5,'warning','open',1,"
            "'ind:__rls_it_a__')"), {"i": iid})
        conn.execute(text(
            "INSERT INTO deviations (tenant_id,indicator_id,direction,value,severity,status,"
            "periods,fingerprint) VALUES ('rls_t2',:i,'above',5,'warning','open',1,"
            "'ind:__rls_it_b__')"), {"i": iid})

        conn.execute(text("DROP ROLE IF EXISTS rls_probe_it"))
        conn.execute(text("CREATE ROLE rls_probe_it NOSUPERUSER"))
        conn.execute(text("GRANT SELECT ON deviations TO rls_probe_it"))

        conn.execute(text("SET ROLE rls_probe_it"))

        def _count():
            return conn.execute(text(
                "SELECT count(*) FROM deviations WHERE fingerprint LIKE 'ind:__rls_it_%'"
            )).scalar()

        conn.execute(text("SELECT set_config('app.current_tenant','default',false)"))
        n_default = _count()
        conn.execute(text("SELECT set_config('app.current_tenant','rls_t2',false)"))
        n_t2 = _count()
        conn.execute(text("SELECT set_config('app.current_tenant','',false)"))
        n_open = _count()
        conn.execute(text("RESET ROLE"))

        assert n_default == 1, "tenant context 'default' must see only its own row"
        assert n_t2 == 1, "tenant context 'rls_t2' must see only its own row"
        assert n_open == 2, "no tenant context must fail open (workers/migrations)"
    finally:
        try:
            conn.execute(text("RESET ROLE"))
        except Exception:
            pass
        trans.rollback()
        conn.close()


def test_rls_request_tenant_reaches_db_guc(db_engine):
    """Regression for the propagation fix: the per-request tenant set in HTTP
    middleware must reach the sync endpoint's DB checkout as app.current_tenant.
    Uses the REAL engine + verify_token + RLS checkout hook (mirrors the
    bind_rls_tenant middleware in api/main.py). A dependency-set would NOT propagate."""
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from core import rls
    from core.database import get_engine  # the engine install_rls hooked
    from api.auth import create_access_token, verify_token, ACCESS_COOKIE_NAME

    app = FastAPI()

    @app.middleware("http")
    async def bind(request: Request, call_next):
        rls.current_tenant.set(None)
        auth = request.headers.get("Authorization", "")
        tok = auth[7:] if auth.startswith("Bearer ") else request.cookies.get(ACCESS_COOKIE_NAME)
        if tok:
            try:
                rls.set_request_tenant(verify_token(tok).tenant_id)
            except Exception:
                pass
        return await call_next(request)

    @app.get("/guc")
    def guc():  # sync endpoint → runs in threadpool, like the real routes
        with get_engine().connect() as c:
            return {"guc": c.execute(text("SELECT current_setting('app.current_tenant', true)")).scalar()}

    client = TestClient(app)
    assert client.get("/guc").json()["guc"] in ("", None)  # anon → fail-open
    tok = create_access_token({"sub": "u", "tenant_id": "acme", "roles": [], "permissions": []})
    assert client.get("/guc", headers={"Authorization": f"Bearer {tok}"}).json()["guc"] == "acme"
    assert client.get("/guc").json()["guc"] in ("", None)  # next anon req → no leak
