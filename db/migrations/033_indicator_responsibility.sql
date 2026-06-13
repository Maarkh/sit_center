-- 033_indicator_responsibility.sql
-- "Responsibility map": mark WHO owns each indicator and WHICH escalation chain applies,
-- so deviations spawned from it auto-assign to the owner and auto-escalate by that chain
-- (instead of leaving assigned_to empty and picking a global default chain).
--
-- Resolution is indicator → goal → tenant default:
--   owner:  indicators.owner_user → indicators.owner_role → goals.owner_role
--   chain:  indicators.escalation_chain_id → goals.escalation_chain_id → first active chain
ALTER TABLE indicators ADD COLUMN IF NOT EXISTS owner_role TEXT;
ALTER TABLE indicators ADD COLUMN IF NOT EXISTS owner_user TEXT;
ALTER TABLE indicators ADD COLUMN IF NOT EXISTS escalation_chain_id UUID
    REFERENCES escalation_chains(id) ON DELETE SET NULL;

-- goals already carry owner_role; give them a chain too for the fallback.
ALTER TABLE goals ADD COLUMN IF NOT EXISTS escalation_chain_id UUID
    REFERENCES escalation_chains(id) ON DELETE SET NULL;
