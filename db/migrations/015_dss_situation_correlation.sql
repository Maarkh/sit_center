-- 015_dss_situation_correlation.sql
-- DSS module M4 — Situation & Correlation (Orient / L2 Comprehension).
-- Turns a stream of isolated deviations (M3) into a Situation: related deviations
-- correlated by time proximity AND the indicator dependency graph, with an impact
-- score (how much downstream is affected) and a root-cause hypothesis (the
-- upstream-most breaching indicator). This is what cuts "alert noise".

-- Directed influence edges between indicators (src влияет на dst).
CREATE TABLE IF NOT EXISTS indicator_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    src_indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    dst_indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    weight NUMERIC NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_dep UNIQUE (tenant_id, src_indicator_id, dst_indicator_id),
    CONSTRAINT chk_dep_no_self CHECK (src_indicator_id <> dst_indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_deps_tenant ON indicator_dependencies (tenant_id);
CREATE INDEX IF NOT EXISTS idx_deps_src ON indicator_dependencies (src_indicator_id);
CREATE INDEX IF NOT EXISTS idx_deps_dst ON indicator_dependencies (dst_indicator_id);


CREATE TABLE IF NOT EXISTS situations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    title TEXT NOT NULL,
    root_cause_indicator_id UUID REFERENCES indicators(id) ON DELETE SET NULL,
    root_cause_hypothesis TEXT,
    impact_score NUMERIC NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'open',         -- open | investigating | resolved | closed
    deviation_count INT NOT NULL DEFAULT 0,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    CONSTRAINT chk_situation_status CHECK (status IN ('open', 'investigating', 'resolved', 'closed'))
);

CREATE INDEX IF NOT EXISTS idx_situations_tenant ON situations (tenant_id);
CREATE INDEX IF NOT EXISTS idx_situations_active ON situations (status) WHERE status IN ('open', 'investigating');

CREATE TRIGGER update_situations_updated_at
    BEFORE UPDATE ON situations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Which deviations belong to a situation (correlation result).
CREATE TABLE IF NOT EXISTS situation_deviations (
    situation_id UUID NOT NULL REFERENCES situations(id) ON DELETE CASCADE,
    deviation_id UUID NOT NULL REFERENCES deviations(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (situation_id, deviation_id)
);

CREATE INDEX IF NOT EXISTS idx_situation_deviations_dev ON situation_deviations (deviation_id);

-- ✅ M4 schema ready.
