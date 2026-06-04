-- 018_dss_deviation_incident.sql
-- Consolidation: the DSS is the single detector; a persistent (chronic) deviation
-- auto-creates a classic Incident (reusing the mature SLA / escalation / i-doit tail).
-- This links a deviation to the incident it spawned, for dedup (one incident per
-- active deviation) and traceability.

ALTER TABLE deviations
    ADD COLUMN IF NOT EXISTS incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_deviations_incident ON deviations (incident_id);

-- ✅ deviation ↔ incident link ready.
