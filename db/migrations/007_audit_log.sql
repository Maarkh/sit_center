-- 007_audit_log.sql
-- Audit log for tracking user actions

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    action TEXT NOT NULL,              -- create, update, delete, login, suppress, etc.
    resource_type TEXT NOT NULL,        -- metric, rule, alert, user, tenant, ml_config, etc.
    resource_id TEXT,
    changes JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log (tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log (username);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log (action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log (resource_type, resource_id);
