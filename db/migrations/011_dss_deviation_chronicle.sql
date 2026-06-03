-- 011_dss_deviation_chronicle.sql
-- DSS module M3 — Deviation Detection & Chronicle.
-- Two-sided corridor breach detection on indicators (M2). A `deviation` is one
-- breach episode (open → acknowledged → resolved). A `chronicle` is the
-- longitudinal summary per indicator: how often it breaches and how long streaks
-- get — the "это повторяется" signal that raises priority and cuts alert noise.

CREATE TABLE IF NOT EXISTS deviations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    dimensions JSONB NOT NULL DEFAULT '{}',
    direction TEXT NOT NULL,                       -- below | above
    value NUMERIC,
    target_low NUMERIC,
    target_high NUMERIC,
    severity TEXT NOT NULL DEFAULT 'warning',      -- warning | critical
    status TEXT NOT NULL DEFAULT 'open',           -- open | acknowledged | resolved
    -- consecutive evaluation cycles this episode has stayed breaching (хроника эпизода)
    periods INT NOT NULL DEFAULT 1,
    fingerprint TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ,
    CONSTRAINT chk_dev_direction CHECK (direction IN ('below', 'above')),
    CONSTRAINT chk_dev_status CHECK (status IN ('open', 'acknowledged', 'resolved'))
);

CREATE INDEX IF NOT EXISTS idx_deviations_indicator ON deviations (indicator_id);
CREATE INDEX IF NOT EXISTS idx_deviations_active ON deviations (status) WHERE status <> 'resolved';
CREATE INDEX IF NOT EXISTS idx_deviations_detected ON deviations (detected_at DESC);
-- At most one active (open|acknowledged) deviation per fingerprint per tenant.
-- This is the upsert target for the evaluation loop.
CREATE UNIQUE INDEX IF NOT EXISTS ux_deviations_active_fp
    ON deviations (tenant_id, fingerprint) WHERE status <> 'resolved';


CREATE TABLE IF NOT EXISTS chronicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    episodes INT NOT NULL DEFAULT 0,               -- distinct breach episodes seen
    total_periods INT NOT NULL DEFAULT 0,          -- cumulative breaching cycles
    max_periods INT NOT NULL DEFAULT 0,            -- longest consecutive streak
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ux_chronicle_fp UNIQUE (tenant_id, fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_chronicles_indicator ON chronicles (indicator_id);

-- ✅ M3 schema ready.
