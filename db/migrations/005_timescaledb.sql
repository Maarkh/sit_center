-- 005_timescaledb.sql
-- Migration: Convert canonical_metrics to TimescaleDB hypertable
-- Replaces manual monthly partitioning with automatic chunking

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Drop existing manual partitions and indexes that conflict
-- (TimescaleDB manages its own chunk indexes)
DROP INDEX IF EXISTS idx_canonical_ts;
DROP INDEX IF EXISTS idx_canonical_metric_ts;

-- Convert canonical_metrics to a hypertable with 7-day chunks
-- migrate_data => true moves existing rows into chunks
SELECT create_hypertable(
    'canonical_metrics',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    migrate_data => true,
    if_not_exists => true
);

-- Re-create indexes on the hypertable
CREATE INDEX IF NOT EXISTS idx_canonical_ts ON canonical_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_metric_ts ON canonical_metrics (metric_name, timestamp DESC);

-- Compression policy: compress chunks older than 30 days
ALTER TABLE canonical_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'metric_name',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('canonical_metrics', INTERVAL '30 days', if_not_exists => true);

-- Retention policy: drop chunks older than 365 days
SELECT add_retention_policy('canonical_metrics', INTERVAL '365 days', if_not_exists => true);

-- Continuous aggregate: replaces manual mv_hourly_region_metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS cagg_hourly_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    metric_name,
    dimensions->>'region' AS region,
    AVG(value) AS avg_value,
    MAX(value) AS max_value,
    MIN(value) AS min_value,
    COUNT(*) AS sample_count
FROM canonical_metrics
WHERE dimensions ? 'region'
GROUP BY hour, metric_name, dimensions->>'region'
WITH NO DATA;

-- Refresh policy for the continuous aggregate. The window (start_offset -
-- end_offset) must be >= 2x the bucket width (1 hour), so use 3h .. 1h = 2h.
-- end_offset = 1 bucket also avoids refreshing the still-incomplete current hour.
SELECT add_continuous_aggregate_policy('cagg_hourly_metrics',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '10 minutes',
    if_not_exists => true
);

-- Drop the old manual materialized view if it exists
DROP MATERIALIZED VIEW IF EXISTS mv_hourly_region_metrics;
