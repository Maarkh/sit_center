-- 020_backfill_incident_escalation_chain.sql
-- DSS-bridge auto-incidents were created without an escalation_chain_id, and
-- check_auto_escalation() skips incidents that have no chain — so they could never
-- auto-escalate. Attach each tenant's default (earliest active) chain to its active
-- incidents that still lack one. Idempotent; a no-op on a fresh DB (no incidents yet).

UPDATE incidents i SET escalation_chain_id = ch.id
FROM (
    SELECT DISTINCT ON (tenant_id) tenant_id, id
    FROM escalation_chains
    WHERE is_active = true
    ORDER BY tenant_id, created_at
) ch
WHERE ch.tenant_id = i.tenant_id
  AND i.escalation_chain_id IS NULL
  AND i.status NOT IN ('resolved', 'closed');

-- ✅ active incidents now carry an escalation chain.
