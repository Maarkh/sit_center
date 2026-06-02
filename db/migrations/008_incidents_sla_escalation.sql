-- 008_incidents_sla_escalation.sql
-- SLA policies, escalation chains, incident enhancements

-- === 1. SLA Policies ===
CREATE TABLE IF NOT EXISTS sla_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    name TEXT NOT NULL,
    priority TEXT NOT NULL,
    response_time_minutes INT NOT NULL,
    resolution_time_minutes INT NOT NULL,
    escalation_after_minutes INT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, priority)
);

INSERT INTO sla_policies (tenant_id, name, priority, response_time_minutes, resolution_time_minutes, escalation_after_minutes) VALUES
    ('default', 'Critical SLA', 'critical', 15, 60, 30),
    ('default', 'High SLA', 'high', 30, 240, 120),
    ('default', 'Medium SLA', 'medium', 60, 480, 240),
    ('default', 'Low SLA', 'low', 120, 1440, 480)
ON CONFLICT DO NOTHING;

-- === 2. Escalation Chains ===
CREATE TABLE IF NOT EXISTS escalation_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS escalation_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID NOT NULL REFERENCES escalation_chains(id) ON DELETE CASCADE,
    level INT NOT NULL,
    notify_role TEXT NOT NULL,
    notify_users JSONB DEFAULT '[]',
    escalate_after_minutes INT NOT NULL,
    UNIQUE(chain_id, level)
);

-- Default escalation chain
INSERT INTO escalation_chains (id, tenant_id, name) VALUES
    ('00000000-0000-0000-0000-000000000001', 'default', 'Default Chain')
ON CONFLICT DO NOTHING;

INSERT INTO escalation_levels (chain_id, level, notify_role, escalate_after_minutes) VALUES
    ('00000000-0000-0000-0000-000000000001', 1, 'operator', 30),
    ('00000000-0000-0000-0000-000000000001', 2, 'manager', 60),
    ('00000000-0000-0000-0000-000000000001', 3, 'director', 120)
ON CONFLICT DO NOTHING;

-- === 3. Enhance incidents table ===
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS sla_policy_id UUID REFERENCES sla_policies(id);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS response_deadline TIMESTAMPTZ;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolution_deadline TIMESTAMPTZ;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS response_breached BOOLEAN DEFAULT false;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolution_breached BOOLEAN DEFAULT false;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS escalation_level INT DEFAULT 0;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS escalation_chain_id UUID REFERENCES escalation_chains(id);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS last_escalated_at TIMESTAMPTZ;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS alert_event_id UUID;

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_priority ON incidents (priority);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned ON incidents (assigned_to);
CREATE INDEX IF NOT EXISTS idx_incidents_open_deadline ON incidents (resolution_deadline)
    WHERE status NOT IN ('resolved', 'closed');

-- === 4. Add acknowledged status to alert_events ===
-- (status already TEXT, just allow new value 'acknowledged')
ALTER TABLE alert_events ADD COLUMN IF NOT EXISTS acknowledged_by TEXT;
ALTER TABLE alert_events ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;
ALTER TABLE alert_events ADD COLUMN IF NOT EXISTS resolved_by TEXT;
