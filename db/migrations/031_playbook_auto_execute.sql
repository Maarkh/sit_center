-- 031_playbook_auto_execute.sql
-- D (auto-remediation): let an operator mark a playbook safe to dispatch WITHOUT a
-- human clicking "accept". When a chronic deviation generates recommendations and the
-- top match is an auto_execute playbook (and the global AUTO_REMEDIATION_ENABLED switch
-- is on and the match is confident enough), the system accepts it automatically and
-- starts the playbook's process. The existing Act→Observe verify (verify_remediation_task)
-- re-measures on completion and escalates to a human if it didn't help.
--
-- Default false: opt-in per playbook AND globally, so nothing auto-runs by surprise.
ALTER TABLE playbooks ADD COLUMN IF NOT EXISTS auto_execute BOOLEAN NOT NULL DEFAULT false;
