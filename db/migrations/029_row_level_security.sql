-- 029_row_level_security.sql
-- Defense-in-depth tenant isolation at the DB layer (FIX-10). The application
-- already filters every query by tenant_id; RLS adds a backstop so a query that
-- forgets the filter (or an injection) still cannot cross tenants.
--
-- Design — FAIL-OPEN when no tenant context is set:
--   * The web layer sets `app.current_tenant` to the caller's tenant per request
--     (core/rls.py, via a connection-pool checkout hook) → RLS restricts to it.
--   * Workers / the collector / migrations legitimately operate ACROSS tenants and
--     set no context → the policy allows all rows, so nothing breaks.
--   * '*' is an explicit bypass sentinel for the same purpose.
-- This is strictly safer than today (no RLS) without changing cross-tenant flows.
--
-- ⚠️ OPS REQUIREMENT: RLS is bypassed by SUPERUSER and BYPASSRLS roles (and, without
-- FORCE, by the table owner). FORCE is set below so the owner is subject too — but the
-- application MUST connect as a NON-superuser, non-BYPASSRLS role for RLS to take
-- effect. Create a dedicated app role in production (see docs/operations.md).

-- NB: TimescaleDB hypertables with columnstore (compression) enabled do NOT support
-- ENABLE ROW LEVEL SECURITY (canonical_metrics). They are skipped — that table is
-- append-only telemetry, already filtered by tenant_id in every query, and far less
-- sensitive than the DSS state tables this policy protects.
DO $$
DECLARE
    t text;
    has_ts boolean;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') INTO has_ts;
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'tenant_id'
        ORDER BY table_name
    LOOP
        IF has_ts AND EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = t
        ) THEN
            CONTINUE;  -- hypertable → RLS unsupported, skip
        END IF;
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', t);
        EXECUTE format(
            'CREATE POLICY tenant_isolation ON %I '
            'USING ('
            '  tenant_id = current_setting(''app.current_tenant'', true) '
            '  OR coalesce(current_setting(''app.current_tenant'', true), '''') IN ('''', ''*'')'
            ') '
            'WITH CHECK ('
            '  tenant_id = current_setting(''app.current_tenant'', true) '
            '  OR coalesce(current_setting(''app.current_tenant'', true), '''') IN ('''', ''*'')'
            ')', t);
    END LOOP;
END $$;

-- ✅ Row-Level Security (fail-open) applied to all tenant_id tables.
