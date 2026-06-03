-- 017_dss_scenarios.sql
-- DSS module M6 — Model & Scenario Management / what-if (Model subsystem).
-- A scenario is a set of assumptions ("indicator X → delta / target value"); running
-- it projects each assumed indicator against its corridor (M2) and estimates the
-- POTENTIAL — the impact avoided (severity × downstream influence, M4) if the
-- assumed change removes a breach. Lets a decision-maker compare "what if we act".

CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    description TEXT,
    situation_id UUID REFERENCES situations(id) ON DELETE SET NULL,
    -- [{ "indicator_id": "...", "mode": "target|delta|delta_pct", "value": 50 }, ...]
    assumptions JSONB NOT NULL DEFAULT '[]',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scenarios_tenant ON scenarios (tenant_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_situation ON scenarios (situation_id);

CREATE TRIGGER update_scenarios_updated_at
    BEFORE UPDATE ON scenarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- One row per scenario run (history of what-if evaluations).
CREATE TABLE IF NOT EXISTS scenario_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    -- [{ indicator_id, baseline, projected, baseline_breach, projected_breach, improved }, ...]
    results JSONB NOT NULL DEFAULT '[]',
    potential_value NUMERIC NOT NULL DEFAULT 0,
    breaches_avoided INT NOT NULL DEFAULT 0,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scenario_results_scenario ON scenario_results (scenario_id, computed_at DESC);

-- ✅ M6 schema ready.
