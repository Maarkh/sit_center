-- init_schema.sql
-- PostgreSQL 12+ (для gen_random_uuid и JSONB функций)

-- UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- === 1. Каноническая таблица метрик ===
-- Основное хранилище всех временных рядов
CREATE TABLE IF NOT EXISTS canonical_metrics (
    id BIGSERIAL,
    metric_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dimensions JSONB NOT NULL DEFAULT '{}',
    tags JSONB NOT NULL DEFAULT '{}',
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- TimescaleDB requires the partitioning column (timestamp) to be part of every
    -- unique index, so the primary key is composite. `id` stays a surrogate via
    -- BIGSERIAL; nothing foreign-keys canonical_metrics(id).
    PRIMARY KEY (id, timestamp)
);

-- 🔍 Критические индексы
CREATE INDEX IF NOT EXISTS idx_canonical_ts ON canonical_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_metric ON canonical_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin ON canonical_metrics USING GIN (dimensions);
CREATE INDEX IF NOT EXISTS idx_canonical_tags_gin ON canonical_metrics USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_canonical_metric_ts ON canonical_metrics (metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_metric ON canonical_metrics ((dimensions::text), metric_name);

-- 📦 Опциональное партиционирование по месяцам (раскомментировать при >10M строк)
-- CREATE TABLE canonical_metrics PARTITION OF canonical_metrics
-- FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
-- (и т.д.)

-- === 2. Метаданные метрик ===
CREATE TABLE IF NOT EXISTS metadata_metrics (
    metric_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    unit TEXT DEFAULT '',
    default_threshold NUMERIC,
    default_critical_threshold NUMERIC,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Триггер обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_metadata_metrics_updated_at
    BEFORE UPDATE ON metadata_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- === 3. Метаданные измерений (dimensions) ===
CREATE TABLE IF NOT EXISTS metadata_dimensions (
    dimension_key TEXT PRIMARY KEY,
    description TEXT,
    allowed_values JSONB,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- === 4. Настройки действий (плагины) ===
CREATE TABLE IF NOT EXISTS metadata_actions (
    id SERIAL PRIMARY KEY,
    action_type TEXT NOT NULL,  -- telegram, webhook, idoit, email, slack, incident
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- === 5. Правила мониторинга (условия + действия) ===
CREATE TABLE IF NOT EXISTS metadata_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    condition JSONB NOT NULL,
    labels JSONB NOT NULL DEFAULT '{}',
    actions JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_metadata_rules_updated_at
    BEFORE UPDATE ON metadata_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_rules_active ON metadata_rules (is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_rules_labels ON metadata_rules USING GIN (labels);


-- === 6. Конфигурации ML ===
CREATE TABLE IF NOT EXISTS metadata_ml_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    metric_name TEXT NOT NULL REFERENCES metadata_metrics(metric_name) ON DELETE CASCADE,
    group_by TEXT[] NOT NULL DEFAULT '{}',
    methods TEXT[] NOT NULL DEFAULT '{"prophet"}',
    method_params JSONB NOT NULL DEFAULT '{}',
    retrain_schedule TEXT DEFAULT '0 3 * * *',
    auto_alert BOOLEAN DEFAULT true,
    alert_severity TEXT DEFAULT 'warning',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_metadata_ml_configs_updated_at
    BEFORE UPDATE ON metadata_ml_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_ml_configs_active_metric ON metadata_ml_configs (is_active, metric_name) WHERE is_active = true;


-- === 7. События алертов (федеральная шина) ===
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES metadata_rules(id) ON DELETE SET NULL,
    ml_config_id UUID REFERENCES metadata_ml_configs(id) ON DELETE SET NULL,
    metric_name TEXT NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}',
    value NUMERIC NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'firing',
    resolved_at TIMESTAMPTZ,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    delivery_attempts INT DEFAULT 0,
    last_error TEXT,
    fingerprint TEXT NOT NULL,
    escalation_level INT DEFAULT 0,
    last_escalation TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_firing ON alert_events (status) WHERE status = 'firing';
CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint ON alert_events (fingerprint);
CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alert_events (rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_ml ON alert_events (ml_config_id);
CREATE INDEX IF NOT EXISTS idx_alerts_metric_ts ON alert_events (metric_name, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_dimensions ON alert_events USING GIN (dimensions);


-- === 8. ML-аномалии (результат работы ML) ===
CREATE TABLE IF NOT EXISTS ml_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ml_config_id UUID NOT NULL REFERENCES metadata_ml_configs(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC NOT NULL,
    predicted NUMERIC,
    residual NUMERIC,
    confidence NUMERIC,
    method TEXT NOT NULL,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ml_ts ON ml_anomalies (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ml_config ON ml_anomalies (ml_config_id);
CREATE INDEX IF NOT EXISTS idx_ml_metric_dim ON ml_anomalies (metric_name, (dimensions::text));
CREATE INDEX IF NOT EXISTS idx_ml_dimensions ON ml_anomalies USING GIN (dimensions);


-- === 9. Инциденты (встроенный трекер или i-doit sync) ===
-- Column set aligned with the application (api/schemas.IncidentCreate, models.Incident,
-- api/routes/incidents.py). The SLA/escalation columns come from 008, i-doit sync from 009.
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    alert_message TEXT NOT NULL,
    metric TEXT NOT NULL,
    region TEXT NOT NULL,
    value TEXT,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_to TEXT,
    started_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    description TEXT,
    alert_event_id UUID REFERENCES alert_events(id) ON DELETE SET NULL,
    external_id TEXT,  -- id в i-doit / Jira и т.д.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_priority ON incidents (priority);
CREATE INDEX IF NOT EXISTS idx_incidents_external ON incidents (external_id);


-- === 10. Комментарии к инцидентам ===
CREATE TABLE IF NOT EXISTS incident_comments (
    id SERIAL PRIMARY KEY,
    incident_id INT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_incident ON incident_comments (incident_id);

-- ✅ Готово. Схема инициализирована.