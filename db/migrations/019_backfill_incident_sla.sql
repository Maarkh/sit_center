-- 019_backfill_incident_sla.sql
-- Backfill SLA deadlines for incidents that were created before the DSS bridge
-- applied an SLA policy (chronic-deviation auto-incidents went straight into the
-- incidents table without calling apply_sla_to_incident, so they showed "SLA: N/A").
--
-- Idempotent and safe on a fresh DB: only touches incidents that still have no
-- response_deadline, and only where an active SLA policy exists for the incident's
-- tenant + priority. Deadlines are derived deterministically from detected_at, the
-- same way core/sla_service.apply_sla_to_incident() computes them.

UPDATE incidents i SET
    sla_policy_id       = p.id,
    response_deadline   = i.detected_at + make_interval(mins => p.response_time_minutes),
    resolution_deadline = i.detected_at + make_interval(mins => p.resolution_time_minutes)
FROM sla_policies p
WHERE p.tenant_id = i.tenant_id
  AND p.priority = i.priority
  AND p.is_active = true
  AND i.response_deadline IS NULL;

-- ✅ legacy incidents now carry response/resolution deadlines.
