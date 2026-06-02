-- 009_idoit_sync.sql
-- i-doit integration: bidirectional incident sync

-- Add external system tracking to incidents
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS external_system TEXT DEFAULT 'idoit';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS external_url TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_incidents_external_id ON incidents (external_id) WHERE external_id IS NOT NULL;

-- i-doit sync log for audit trail of sync operations
CREATE TABLE IF NOT EXISTS idoit_sync_log (
    id BIGSERIAL PRIMARY KEY,
    incident_id INT REFERENCES incidents(id) ON DELETE CASCADE,
    direction TEXT NOT NULL,  -- 'push' or 'pull'
    action TEXT NOT NULL,     -- 'create', 'status_update', 'assign', 'comment'
    payload JSONB,
    response JSONB,
    success BOOLEAN NOT NULL DEFAULT false,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_idoit_sync_incident ON idoit_sync_log (incident_id);
