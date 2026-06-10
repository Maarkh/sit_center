-- 026_deviation_severity_score.sql
-- DSS M3: a rankable, continuous severity score alongside the warning/critical label,
-- so the cockpit / NBA can prioritise "which breach is worse" instead of two buckets.
-- score = breach margin / reference scale, boosted by persistence (periods).

ALTER TABLE deviations ADD COLUMN IF NOT EXISTS severity_score NUMERIC;

CREATE INDEX IF NOT EXISTS idx_deviations_tenant_score
    ON deviations (tenant_id, severity_score DESC)
    WHERE status <> 'resolved';

-- ✅ deviations.severity_score ready.
