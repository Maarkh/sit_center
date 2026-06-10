-- 024_http_push_key_hash.sql
-- http_push api keys are now stored as a SHA-256 hash (config->>'api_key_sha256'),
-- never as plaintext. Re-point the lookup index from the old plaintext key.

DROP INDEX IF EXISTS idx_data_sources_api_key;

CREATE INDEX IF NOT EXISTS idx_data_sources_api_key_hash
    ON data_sources ((config->>'api_key_sha256'))
    WHERE type = 'http_push';

-- ✅ http_push api_key hash lookup index ready.
