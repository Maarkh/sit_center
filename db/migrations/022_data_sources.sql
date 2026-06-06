-- 022_data_sources.sql
-- M1 Ingestion: an admin-managed registry of WHERE metrics come from. Each source
-- declares a transport type and a transport-specific config (jsonb):
--   host_agent — psutil metrics of the host running the collector
--                config: {"metrics": ["cpu_usage","mem_usage",...], "sample_seconds": 5}
--   http_pull  — collector GETs a JSON endpoint on an interval and extracts values
--                config: {"url","method","headers","token","interval_seconds","metric_map":[{"json_path","metric_name"}]}
--   kafka      — the kafka consumer subscribes to the declared topic(s)
--                config: {"topic","bootstrap_servers","sasl_password"}
-- The collector (scripts/monitor_cpu.py) and core/kafka_consumer.py read ENABLED
-- sources from this table at runtime instead of hardcoding — so adding/editing a
-- source in the UI changes what gets ingested, live. canonical_metrics.source stays
-- free text: it carries the source NAME (no FK on the hypertable).

CREATE TABLE IF NOT EXISTS data_sources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,                      -- host_agent | http_pull | kafka
    config      JSONB NOT NULL DEFAULT '{}'::jsonb, -- transport-specific
    enabled     BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_data_sources_tenant ON data_sources (tenant_id);
CREATE INDEX IF NOT EXISTS idx_data_sources_type_enabled ON data_sources (tenant_id, type, enabled);

-- A sensible default so a fresh install collects host CPU/RAM out of the box (same
-- metrics the collector used to hardcode), now driven by this registry.
INSERT INTO data_sources (tenant_id, name, type, config, enabled)
VALUES ('default', 'Local host', 'host_agent',
        '{"metrics": ["cpu_usage", "mem_usage"], "sample_seconds": 5}'::jsonb, true)
ON CONFLICT (tenant_id, name) DO NOTHING;

-- ✅ data_sources registry ready.
