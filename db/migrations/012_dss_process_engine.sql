-- 012_dss_process_engine.sql
-- DSS module M8 (MVP) — executable regulation / workflow engine.
-- A ProcessTemplate is a reusable regulation: an ordered set of steps. Steps that
-- share a step_order run in parallel; different orders run sequentially. A
-- ProcessInstance binds a template to a situation (incident or deviation) and
-- snapshots its steps into step_assignments (the live, reportable work items).

CREATE TABLE IF NOT EXISTS process_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ptemplates_tenant ON process_templates (tenant_id);

CREATE TRIGGER update_process_templates_updated_at
    BEFORE UPDATE ON process_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE IF NOT EXISTS process_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    template_id UUID NOT NULL REFERENCES process_templates(id) ON DELETE CASCADE,
    step_order INT NOT NULL,                        -- same order = parallel; lower runs first
    name TEXT NOT NULL,
    step_type TEXT NOT NULL DEFAULT 'sequential',   -- sequential | parallel (intent/label)
    assignee_role TEXT,
    checklist JSONB NOT NULL DEFAULT '[]',          -- ["проверить X", "перезапустить Y"]
    due_after_minutes INT,                          -- SLA: due_at = activation + this
    CONSTRAINT chk_step_type CHECK (step_type IN ('sequential', 'parallel'))
);

CREATE INDEX IF NOT EXISTS idx_psteps_template ON process_steps (template_id, step_order);


CREATE TABLE IF NOT EXISTS process_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    template_id UUID NOT NULL REFERENCES process_templates(id),
    incident_id INT REFERENCES incidents(id) ON DELETE SET NULL,
    deviation_id UUID REFERENCES deviations(id) ON DELETE SET NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'running',          -- running | completed | cancelled
    started_by TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT chk_instance_status CHECK (status IN ('running', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_pinstances_tenant ON process_instances (tenant_id);
CREATE INDEX IF NOT EXISTS idx_pinstances_status ON process_instances (status) WHERE status = 'running';
CREATE INDEX IF NOT EXISTS idx_pinstances_incident ON process_instances (incident_id);
CREATE INDEX IF NOT EXISTS idx_pinstances_deviation ON process_instances (deviation_id);


CREATE TABLE IF NOT EXISTS step_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    instance_id UUID NOT NULL REFERENCES process_instances(id) ON DELETE CASCADE,
    step_id UUID REFERENCES process_steps(id) ON DELETE SET NULL,
    step_order INT NOT NULL,
    step_type TEXT NOT NULL DEFAULT 'sequential',
    name TEXT NOT NULL,
    assignee_role TEXT,
    assignee TEXT,
    checklist_state JSONB NOT NULL DEFAULT '[]',     -- [{"item": "...", "done": false}]
    status TEXT NOT NULL DEFAULT 'pending',           -- pending | active | in_progress | done | skipped
    report TEXT,
    due_after_minutes INT,                            -- snapshot of the step SLA at instantiation
    due_at TIMESTAMPTZ,                               -- set on activation = activated_at + due_after_minutes
    escalated BOOLEAN NOT NULL DEFAULT false,
    started_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    completed_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_assignment_status
        CHECK (status IN ('pending', 'active', 'in_progress', 'done', 'skipped'))
);

CREATE INDEX IF NOT EXISTS idx_stepasg_instance ON step_assignments (instance_id, step_order);
CREATE INDEX IF NOT EXISTS idx_stepasg_active ON step_assignments (status)
    WHERE status IN ('active', 'in_progress');

-- ✅ M8 schema ready.
