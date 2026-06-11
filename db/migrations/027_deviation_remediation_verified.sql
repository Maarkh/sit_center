-- 027_deviation_remediation_verified.sql
-- DSS OODA loop closure (Act → Observe): when a remediation process (M8) tied to a
-- deviation completes, a delayed task re-measures the indicator and records whether
-- the deviation actually cleared — so "we ran the playbook" is distinguished from
-- "the playbook worked". Without this the loop was open: Act had no control measure.
--   remediation_outcome:     'confirmed' (cleared) | 'persisted' (still breaching)
--   remediation_verified_at: when the post-process re-check ran (NULL = never checked)

ALTER TABLE deviations ADD COLUMN IF NOT EXISTS remediation_verified_at TIMESTAMPTZ;
ALTER TABLE deviations ADD COLUMN IF NOT EXISTS remediation_outcome TEXT;

-- ✅ deviations.remediation_verified_at / remediation_outcome ready.
