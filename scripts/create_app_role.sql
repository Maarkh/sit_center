-- scripts/create_app_role.sql
-- Provision the least-privilege application DB role required for Row-Level Security
-- (migration 029) to actually enforce. PostgreSQL BYPASSES RLS for SUPERUSER /
-- BYPASSRLS roles, so the app (web + workers) must connect as THIS role, while
-- migrations keep running as the owner/superuser.
--
-- Run as the DB owner/superuser, passing the password:
--   psql "$ADMIN_DATABASE_URL" -v app_password="'<strong-password>'" -f scripts/create_app_role.sql
-- Then point the app services' DATABASE_URL at sitcenter_app and keep migrations on
-- the owner role. Verify: the app startup log must NOT show the "RLS is BYPASSED"
-- warning (core/rls.py:warn_if_rls_bypassed).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sitcenter_app') THEN
        EXECUTE format('CREATE ROLE sitcenter_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB '
                       'NOCREATEROLE PASSWORD %s', :'app_password');
    ELSE
        EXECUTE format('ALTER ROLE sitcenter_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD %s',
                       :'app_password');
    END IF;
END $$;

GRANT CONNECT ON DATABASE current_catalog TO sitcenter_app;  -- (run \c first if needed)
GRANT USAGE ON SCHEMA public TO sitcenter_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sitcenter_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sitcenter_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sitcenter_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sitcenter_app;

-- ✅ sitcenter_app ready — point the app's DATABASE_URL at it; RLS now enforces.
