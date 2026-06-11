-- 028_forecast_accuracy.sql
-- DSS M5 model-drift monitoring. Forecasts are already persisted (M5 writes a
-- snapshot per run into `forecasts`); once a forecast point's timestamp passes we
-- have the ACTUAL value to score it against. This table records the rolling
-- prediction error (MAE / RMSE / MAPE) per indicator-metric so a degrading model
-- is visible (cockpit / Grafana) and alertable, instead of silently drifting.

CREATE TABLE IF NOT EXISTS forecast_accuracy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    window_days INT NOT NULL,
    sample_size INT NOT NULL,           -- forecast points matched to an actual
    mae NUMERIC,
    rmse NUMERIC,
    mape NUMERIC,                       -- percent; NULL when every actual was 0
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecast_accuracy_lookup
    ON forecast_accuracy (tenant_id, indicator_id, computed_at DESC);

-- ✅ forecast_accuracy ready.
