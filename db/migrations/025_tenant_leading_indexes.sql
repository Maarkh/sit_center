-- 025_tenant_leading_indexes.sql
-- Multi-tenant hot reads filter (tenant_id, metric_name, timestamp). The hypertable
-- had a tenant index and a (metric_name, timestamp) index but not a tenant-LEADING
-- composite, so the tenant filter ran after the index scan. Add the composite — and
-- drop redundant/duplicate indexes so the high-ingest table's write cost doesn't grow.

-- canonical_metrics: drop a duplicate (timestamp) index and a prefix-redundant one.
DROP INDEX IF EXISTS idx_canonical_ts;       -- duplicate of canonical_metrics_timestamp_idx
DROP INDEX IF EXISTS idx_canonical_metric;   -- prefix-redundant with idx_canonical_metric_ts
CREATE INDEX IF NOT EXISTS idx_canonical_tenant_metric_ts
    ON canonical_metrics (tenant_id, metric_name, "timestamp" DESC);

-- alert_events: drop a duplicate (metric_name, event_time) index; add tenant-leading.
DROP INDEX IF EXISTS idx_alerts_metric_ts;   -- duplicate of idx_alerts_metric_time
CREATE INDEX IF NOT EXISTS idx_alerts_tenant_metric_time
    ON alert_events (tenant_id, metric_name, event_time DESC);

-- incidents: drop a redundant external-id index; add tenant-leading status index for
-- the open-incidents list.
DROP INDEX IF EXISTS idx_incidents_external;  -- superseded by partial idx_incidents_external_id
CREATE INDEX IF NOT EXISTS idx_incidents_tenant_status
    ON incidents (tenant_id, status);

-- ✅ tenant-leading composites in place; redundant indexes removed.
