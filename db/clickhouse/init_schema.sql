-- ClickHouse schema for Situational Center analytics (OLAP)

CREATE DATABASE IF NOT EXISTS sit_center;

-- Metrics table (MergeTree, partitioned by month + tenant)
CREATE TABLE IF NOT EXISTS sit_center.metrics
(
    metric_name   String,
    value         Float64,
    timestamp     DateTime64(3, 'UTC'),
    dimensions    String,   -- JSON string
    tags          String,   -- JSON string
    source        String DEFAULT 'pg_sync',
    tenant_id     String DEFAULT 'default',
    ingested_at   DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(timestamp))
ORDER BY (tenant_id, metric_name, timestamp)
TTL toDateTime(timestamp) + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Alerts table
CREATE TABLE IF NOT EXISTS sit_center.alerts
(
    id            String,
    metric_name   String,
    dimensions    String,   -- JSON string
    value         Float64,
    event_time    DateTime64(3, 'UTC'),
    status        String DEFAULT 'firing',
    fingerprint   String,
    tenant_id     String DEFAULT 'default',
    ingested_at   DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(event_time))
ORDER BY (tenant_id, metric_name, event_time)
TTL toDateTime(event_time) + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;
