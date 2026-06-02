-- 004_performance_indexes.sql
-- Индексы для производительности

BEGIN;

-- Индекс для alert_events (без несуществующей колонки priority)
CREATE INDEX IF NOT EXISTS idx_alerts_status_time
ON alert_events (status, event_time DESC)
WHERE status = 'firing';

-- Индекс для быстрого поиска по fingerprint
CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint_status
ON alert_events (fingerprint, status);

-- Индекс для метрик по времени
CREATE INDEX IF NOT EXISTS idx_alerts_metric_time
ON alert_events (metric_name, event_time DESC);

COMMIT;