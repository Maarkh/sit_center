-- 023_http_push_index.sql
-- M1 push ingestion: external agents POST metrics to /api/v1/ingest/metrics with a
-- per-source API key (X-API-KEY). The ingestion route looks the source up by
-- config->>'api_key' on every request, so index that expression for http_push rows.

CREATE INDEX IF NOT EXISTS idx_data_sources_api_key
    ON data_sources ((config->>'api_key'))
    WHERE type = 'http_push';

-- ✅ http_push api_key lookup index ready.
