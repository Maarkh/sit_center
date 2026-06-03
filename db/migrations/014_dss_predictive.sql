-- 014_dss_predictive.sql
-- DSS module M5 — Forecasting & Predictive Alerts (Project / L3 Projection).
-- Closes the existing on-demand forecast into the loop: a periodic task projects each
-- indicator forward and, if the forecast (or its confidence band) is predicted to leave
-- the target corridor within the horizon, raises a PREDICTIVE alert — "act early",
-- BEFORE the deviation happens. This is the differentiator vs ИСУ (no real-time forecast).

-- Forecast snapshot (for cockpit charts + audit of what the prediction saw).
CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    horizon_hours INT NOT NULL,
    model_version TEXT,
    points JSONB NOT NULL DEFAULT '[]',   -- [{ts, yhat, yhat_low, yhat_high}, ...]
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecasts_indicator ON forecasts (indicator_id, generated_at DESC);


CREATE TABLE IF NOT EXISTS predictive_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    direction TEXT NOT NULL,                       -- below | above
    projected_value NUMERIC,
    target_low NUMERIC,
    target_high NUMERIC,
    breach_eta TIMESTAMPTZ,                         -- when the corridor is predicted to break
    horizon_hours INT NOT NULL,
    -- 'high' = central forecast (yhat) breaches; 'medium' = only the confidence band does.
    confidence TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'open',            -- open | acknowledged | resolved
    fingerprint TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ,
    CONSTRAINT chk_pred_direction CHECK (direction IN ('below', 'above')),
    CONSTRAINT chk_pred_status CHECK (status IN ('open', 'acknowledged', 'resolved')),
    CONSTRAINT chk_pred_confidence CHECK (confidence IN ('medium', 'high'))
);

CREATE INDEX IF NOT EXISTS idx_predalerts_indicator ON predictive_alerts (indicator_id);
CREATE INDEX IF NOT EXISTS idx_predalerts_active ON predictive_alerts (status) WHERE status <> 'resolved';
CREATE UNIQUE INDEX IF NOT EXISTS ux_predalerts_active_fp
    ON predictive_alerts (tenant_id, fingerprint) WHERE status <> 'resolved';

-- ✅ M5 schema ready.
