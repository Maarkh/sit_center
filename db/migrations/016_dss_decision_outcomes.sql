-- 016_dss_decision_outcomes.sql
-- DSS module M10 — Decision Log & Learning Loop (Learn).
-- The accepted recommendation (M7) already records the decision: chosen alternative,
-- launched process (M8), decided_by/at. M10 adds the missing half — the OUTCOME:
-- did the decision actually resolve the situation, and with what effect. Aggregated
-- per playbook, this becomes a win-rate that feeds back into recommendation ranking.

CREATE TABLE IF NOT EXISTS decision_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    -- The decision = the accepted recommendation.
    recommendation_id UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
    resolved BOOLEAN NOT NULL,                 -- did the action resolve the situation?
    effect_value NUMERIC,                      -- optional measured effect / potential realised
    note TEXT,
    auto BOOLEAN NOT NULL DEFAULT false,       -- system-derived vs operator-recorded
    evaluated_by TEXT,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- One outcome per decision.
    CONSTRAINT uq_outcome_recommendation UNIQUE (recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_tenant ON decision_outcomes (tenant_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_recommendation ON decision_outcomes (recommendation_id);

-- ✅ M10 schema ready.
