-- 013_dss_knowledge_recommendation.sql
-- DSS module M7 — Knowledge Base & Recommendation (Design + Choice / Next-Best-Action).
-- A playbook is a reusable response to a class of deviation: matching rules
-- (severity / direction / indicator scope), a checklist of recommended actions, and
-- optionally the process_template (M8) that executes it. The recommendation engine
-- scores matching playbooks for a deviation and ranks them as alternatives; accepting
-- one instantiates its process (the Choice → Act bridge) and records the decision.

CREATE TABLE IF NOT EXISTS playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    description TEXT,
    -- Matching rules. NULL = matches any.
    trigger_severity TEXT,                          -- NULL | warning | critical
    trigger_direction TEXT,                         -- NULL | below | above
    -- Effect/potential of running this playbook (the ИСУ "Потенциал" — drives ranking).
    effect_score NUMERIC NOT NULL DEFAULT 1.0,
    -- Optional regulation to execute when the recommendation is accepted.
    process_template_id UUID REFERENCES process_templates(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_playbook_severity CHECK (trigger_severity IS NULL OR trigger_severity IN ('warning', 'critical')),
    CONSTRAINT chk_playbook_direction CHECK (trigger_direction IS NULL OR trigger_direction IN ('below', 'above'))
);

CREATE INDEX IF NOT EXISTS idx_playbooks_tenant ON playbooks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_playbooks_active ON playbooks (is_active) WHERE is_active = true;

CREATE TRIGGER update_playbooks_updated_at
    BEFORE UPDATE ON playbooks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Recommended actions (checklist / mentoring steps) for a playbook.
CREATE TABLE IF NOT EXISTS playbook_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    playbook_id UUID NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
    action_order INT NOT NULL,
    action TEXT NOT NULL,
    checklist JSONB NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_pbactions_playbook ON playbook_actions (playbook_id, action_order);


-- Indicator scope. If a playbook has NO rows here, it applies to every indicator
-- (generic). Otherwise it only matches the listed indicators (more specific → higher score).
CREATE TABLE IF NOT EXISTS playbook_indicators (
    playbook_id UUID NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    PRIMARY KEY (playbook_id, indicator_id)
);


-- Generated recommendations (ranked alternatives) for a deviation / incident.
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    deviation_id UUID REFERENCES deviations(id) ON DELETE CASCADE,
    incident_id INT REFERENCES incidents(id) ON DELETE CASCADE,
    playbook_id UUID REFERENCES playbooks(id) ON DELETE SET NULL,
    rank INT NOT NULL,
    score NUMERIC NOT NULL,
    confidence NUMERIC NOT NULL,
    rationale TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',         -- proposed | accepted | dismissed
    process_instance_id UUID REFERENCES process_instances(id) ON DELETE SET NULL,
    decided_by TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_reco_status CHECK (status IN ('proposed', 'accepted', 'dismissed'))
);

CREATE INDEX IF NOT EXISTS idx_recos_deviation ON recommendations (deviation_id);
CREATE INDEX IF NOT EXISTS idx_recos_incident ON recommendations (incident_id);
CREATE INDEX IF NOT EXISTS idx_recos_status ON recommendations (status);

-- ✅ M7 schema ready.
