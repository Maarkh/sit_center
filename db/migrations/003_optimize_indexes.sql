-- 003_optimize_indexes.sql
-- Создание оптимизированных индексов для canonical_metrics

BEGIN;

-- 1. Композитный индекс: metric_name + timestamp + region (для временных запросов)
CREATE INDEX IF NOT EXISTS idx_canonical_metric_ts_region
ON canonical_metrics (
    metric_name,
    timestamp DESC,
    (dimensions->>'region')
);

-- 2. GIN индекс для полнотекстового поиска по dimensions (уже создан в init, пропускаем)
-- CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin
-- ON canonical_metrics USING GIN (dimensions jsonb_path_ops);

-- 3. GIN индекс для tags (уже создан в init, пропускаем)
-- CREATE INDEX IF NOT EXISTS idx_canonical_tags_gin
-- ON canonical_metrics USING GIN (tags jsonb_path_ops);

-- 4. Индекс для фильтрации по source
CREATE INDEX IF NOT EXISTS idx_canonical_source
ON canonical_metrics (source)
WHERE source IS NOT NULL;

-- 5. Индекс для недавних данных
CREATE INDEX IF NOT EXISTS idx_canonical_recent
ON canonical_metrics (timestamp DESC, metric_name);

-- 6. Индекс для агрегационных запросов
CREATE INDEX IF NOT EXISTS idx_canonical_agg
ON canonical_metrics (
    metric_name,
    (dimensions->>'region'),
    timestamp
);

COMMIT;