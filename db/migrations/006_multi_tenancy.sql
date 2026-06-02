-- 006_multi_tenancy.sql
-- Add tenant_id to all tables and create RBAC tables

-- === 1. Tenants table ===
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default tenant
INSERT INTO tenants (id, name) VALUES ('default', 'Default Tenant')
ON CONFLICT DO NOTHING;

-- === 2. Users table ===
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    password_hash TEXT,
    tenant_id TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    auth_provider TEXT DEFAULT 'local',  -- local, ldap, oidc
    external_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tenant ON users (tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- === 3. Roles table ===
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    permissions JSONB NOT NULL DEFAULT '[]',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant ON roles (tenant_id);

-- === 4. User-Role mapping ===
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- === 5. Default roles ===
INSERT INTO roles (name, tenant_id, permissions, description) VALUES
    ('admin', 'default', '["read:metrics","write:metrics","read:rules","write:rules","read:alerts","write:alerts","read:ml","write:ml","admin:tenants","admin:users","read:audit"]', 'Full admin access'),
    ('operator', 'default', '["read:metrics","read:rules","read:alerts","write:alerts","read:ml"]', 'Operator with alert management'),
    ('viewer', 'default', '["read:metrics","read:rules","read:alerts"]', 'Read-only viewer')
ON CONFLICT DO NOTHING;

-- === 6. Add tenant_id columns to existing tables ===

-- canonical_metrics
ALTER TABLE canonical_metrics ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_canonical_tenant ON canonical_metrics (tenant_id);

-- metadata_metrics
ALTER TABLE metadata_metrics ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

-- metadata_dimensions
ALTER TABLE metadata_dimensions ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

-- metadata_rules
ALTER TABLE metadata_rules ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_rules_tenant ON metadata_rules (tenant_id);

-- metadata_ml_configs
ALTER TABLE metadata_ml_configs ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_ml_configs_tenant ON metadata_ml_configs (tenant_id);

-- alert_events
ALTER TABLE alert_events ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alert_events (tenant_id);

-- ml_anomalies
ALTER TABLE ml_anomalies ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_ml_anomalies_tenant ON ml_anomalies (tenant_id);

-- incidents
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_incidents_tenant ON incidents (tenant_id);

-- incident_comments
ALTER TABLE incident_comments ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
