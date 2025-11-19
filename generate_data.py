# generate_data.py
"""
Генератор тестовых данных и инициализатор метаданных для Situational Center v2.

Запуск:
    python generate_data.py --init-db --fill-sample --init-metadata
"""

import argparse
import random
import pandas as pd
from datetime import datetime, timedelta, timezone
import json
from config import settings, logger, mask_secrets
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from core.database import get_engine
from core.config_service import ConfigService
from core.locking import global_lock
import io
import psycopg2
from psycopg2 import sql

# --- 1. Схема БД: DDL ---
INIT_SCHEMA_SQL = """
-- 1. Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Основная таблица данных
CREATE TABLE IF NOT EXISTS canonical_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dimensions JSONB NOT NULL DEFAULT '{}',
    tags JSONB NOT NULL DEFAULT '{}',
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_canonical_ts ON canonical_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_metric ON canonical_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin ON canonical_metrics USING GIN (dimensions);
CREATE INDEX IF NOT EXISTS idx_canonical_tags_gin ON canonical_metrics USING GIN (tags);

-- 3. Метаданные метрик
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

-- 4. Метаданные измерений
CREATE TABLE IF NOT EXISTS metadata_dimensions (
    dimension_key TEXT PRIMARY KEY,
    description TEXT,
    allowed_values JSONB,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Правила
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

-- 6. ML-конфиги
CREATE TABLE IF NOT EXISTS metadata_ml_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    metric_name TEXT NOT NULL REFERENCES metadata_metrics(metric_name),
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

-- 7. Алерты
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES metadata_rules(id),
    ml_config_id UUID REFERENCES metadata_ml_configs(id),
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

-- 8. ML-аномалии
CREATE TABLE IF NOT EXISTS ml_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ml_config_id UUID NOT NULL REFERENCES metadata_ml_configs(id),
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

-- 9. Таблица конфигураций (для ConfigService)
CREATE TABLE IF NOT EXISTS config_tables (
    name TEXT PRIMARY KEY,
    model_class TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    ttl INTEGER NOT NULL DEFAULT 300,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    schema_name TEXT DEFAULT 'public'
);
"""

def bulk_insert_canonical_metrics(engine, records: list):
    if not records:
        return 0
    
    buf = io.StringIO()
    for r in records:
        metric_name = r.get("metric_name") or ""
        value = r.get("value")
        ts = r.get("timestamp").isoformat() if r.get("timestamp") is not None else ""
        dims = json.dumps(r.get("dimensions", {}), ensure_ascii=False)
        tags = json.dumps(r.get("tags", {}), ensure_ascii=False)
        source = r.get("source") or ""
        val_field = r["value"] if r["value"] is not None else "\\N"
        buf.write(f"{metric_name}\t{val_field}\t{ts}\t{dims}\t{tags}\t{source}\n")
    
    buf.seek(0)
    conn = engine.raw_connection()
    cur = None
    try:
        cur = conn.cursor()
        copy_sql = """
        COPY canonical_metrics (metric_name, value, timestamp, dimensions, tags, source)
        FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')
        """
        cur.copy_expert(copy_sql, buf)
        conn.commit()
        return len(records)
    except Exception as e:
        conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        conn.close()

def init_db_schema(engine):
    """Инициализирует схему базы данных."""
    logger.info("🔧 Инициализация схемы БД...")
    with engine.connect() as conn:
        conn.execute(text(INIT_SCHEMA_SQL))
        conn.commit()
    logger.info("✅ Схема БД инициализирована.")


# --- 2. Метаданные: метрики, dimensions, правила ---
METRICS_DATA = [
    {"metric_name": "api_latency_p99", "display_name": "Задержка API (P99)", "unit": "ms", "default_threshold": 500},
    {"metric_name": "db_connections", "display_name": "Подключений к БД", "unit": "count", "default_threshold": 100},
    {"metric_name": "error_rate", "display_name": "Доля ошибок", "unit": "%", "default_threshold": 1.0},
    {"metric_name": "rps", "display_name": "Запросов в секунду", "unit": "rps", "default_threshold": 1000},
]

DIMENSIONS_DATA = [
    {"dimension_key": "region", "description": "Регион РФ", "allowed_values": ["RU-MOW", "RU-SPE", "RU-ROS"]},
    {"dimension_key": "service", "description": "Микросервис", "allowed_values": ["auth", "billing", "gateway", "notification"]},
    {"dimension_key": "dc", "description": "Дата-центр", "allowed_values": ["mos1", "spb1", "ekb1"]},
    {"dimension_key": "env", "description": "Окружение", "allowed_values": ["prod", "stage"]},
]

RULES_DATA = [
    {
        "name": "HighLatencyCritical",
        "description": "Критичное время отклика API",
        "condition": {
            "expr": "api_latency_p99{service=~\"auth|gateway\", env=\"prod\"} > 800",
            "for": "5m",
            "eval": "1m"
        },
        "labels": {"severity": "critical", "team": "infra"},
        "actions": [
            {"type": "telegram", "config": {"channel": "critical"}},
            {"type": "webhook", "config": {"url": "http://webhook-receiver:9000/webhook/grafana"}}
        ]
    },
    {
        "name": "ErrorRateWarning",
        "description": "Рост ошибок",
        "condition": {
            "expr": "error_rate > 0.5",
            "for": "10m",
            "eval": "1m"
        },
        "labels": {"severity": "warning", "team": "backend"},
        "actions": [{"type": "telegram", "config": {"channel": "warning"}}]
    }
]

ML_CONFIGS_DATA = [
    {
        "name": "ML: Latency P99 per service/dc",
        "metric_name": "api_latency_p99",
        "group_by": ["service", "dc"],
        "methods": ["prophet"],
        "method_params": {"prophet": {"changepoint_prior_scale": 0.05}},
        "retrain_schedule": "0 3 * * *",
        "auto_alert": True,
        "alert_severity": "warning"
    },
    {
        "name": "ML: Error Rate",
        "metric_name": "error_rate",
        "group_by": ["service"],
        "methods": ["lstm"],
        "method_params": {"lstm": {"window_size": 24}},
        "auto_alert": True,
        "alert_severity": "critical"
    }
]


def insert_metadata(engine):
    """Заполняет таблицы метаданных."""
    logger.info("🔧 Заполнение метаданных...")

    with engine.begin() as conn:
        # Метрики
        for m in METRICS_DATA:
            conn.execute(text("""
                INSERT INTO metadata_metrics (metric_name, display_name, unit, default_threshold, is_active)
                VALUES (:metric_name, :display_name, :unit, :default_threshold, true)
                ON CONFLICT (metric_name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    unit = EXCLUDED.unit,
                    default_threshold = EXCLUDED.default_threshold,
                    is_active = true
            """), m)

        # Измерения
        for d in DIMENSIONS_DATA:
            conn.execute(text("""
                INSERT INTO metadata_dimensions (dimension_key, description, allowed_values, is_required)
                VALUES (:dimension_key, :description, :allowed_values, false)
                ON CONFLICT (dimension_key) DO UPDATE SET
                    description = EXCLUDED.description,
                    allowed_values = EXCLUDED.allowed_values
            """), {**d, "allowed_values": json.dumps(d["allowed_values"])})

        # Правила
        for r in RULES_DATA:
            conn.execute(text("""
                INSERT INTO metadata_rules (name, description, condition, labels, actions, is_active)
                VALUES (:name, :description, :condition, :labels, :actions, true)
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    condition = EXCLUDED.condition,
                    labels = EXCLUDED.labels,
                    actions = EXCLUDED.actions,
                    is_active = true
            """), {
                "name": r["name"],
                "description": r["description"],
                "condition": json.dumps(r["condition"]),
                "labels": json.dumps(r["labels"]),
                "actions": json.dumps(r["actions"])
            })

        # ML-конфиги
        for c in ML_CONFIGS_DATA:
            conn.execute(text("""
                INSERT INTO metadata_ml_configs (
                    name, metric_name, group_by, methods, method_params,
                    retrain_schedule, auto_alert, alert_severity, is_active
                ) VALUES (
                    :name, :metric_name, :group_by, :methods, :method_params,
                    :retrain_schedule, :auto_alert, :alert_severity, true
                )
                ON CONFLICT (name) DO UPDATE SET
                    metric_name = EXCLUDED.metric_name,
                    group_by = EXCLUDED.group_by,
                    methods = EXCLUDED.methods,
                    method_params = EXCLUDED.method_params,
                    is_active = true
            """), {
                "name": c["name"],
                "metric_name": c["metric_name"],
                "group_by": c["group_by"],
                "methods": c["methods"],
                "method_params": json.dumps(c.get("method_params", {})),
                "retrain_schedule": c.get("retrain_schedule", "0 3 * * *"),
                "auto_alert": c.get("auto_alert", True),
                "alert_severity": c.get("alert_severity", "warning")
            })

        # config_tables
        conn.execute(text("""
            INSERT INTO config_tables (name, model_class, cache_key, ttl, description, is_active)
            VALUES
                ('metrics', 'core.models.Metric', 'config:metrics', 300, 'Метрики', true),
                ('dimensions', 'core.models.Dimension', 'config:dimensions', 600, 'Измерения', true)
            ON CONFLICT (name) DO NOTHING
        """))

    logger.info("✅ Метаданные заполнены.")

# После init_metadata()
def init_ml_configs(engine):
    from core.models import MetadataMLConfig
    Session = sessionmaker(bind=engine)
    with Session() as session:
        existing = session.query(MetadataMLConfig).count()
        if existing > 0:
            return

        configs = [
            MetadataMLConfig(
                name="Error Rate Anomaly (Region)",
                metric_name="error_rate",
                group_by=["region"],
                methods=["prophet", "lstm"],
                auto_alert=True,
                alert_severity="critical"
            ),
            MetadataMLConfig(
                name="Latency P99 (Region)",
                metric_name="api_latency_p99",
                group_by=["region"],
                methods=["prophet"],
                auto_alert=True
            )
        ]
        session.add_all(configs)
        session.commit()
        logger.info("ML-конфиги инициализированы")

# --- 3. Генерация данных в canonical_metrics ---
def generate_sample_data(engine, hours: int = 24, points_per_hour: int = 4):
    """Генерирует синтетические данные в canonical_metrics."""
    logger.info(f"📊 Генерация синтетических данных за {hours} часов ({points_per_hour} точек/час)...")

    # Базовые параметры
    regions = ["RU-MOW", "RU-SPE", "RU-ROS"]
    services = ["auth", "billing", "gateway"]
    dcs = ["mos1", "spb1"]
    env = "prod"

    now = datetime.now(timezone.utc)
    data = []

    for hour_offset in range(hours * points_per_hour):
        ts = now - timedelta(minutes=15 * hour_offset)  # шаг 15 мин

        for region in regions:
            for service in services:
                for dc in dcs:
                    # Основные метрики
                    latency = max(200, random.gauss(400, 100) + 50 * hour_offset % 600)
                    if hour_offset % 20 == 0:  # имитация аномалии раз в 5 часов
                        latency *= 2.5

                    db_conn = max(10, random.gauss(50, 20) + 5 * hour_offset % 100)
                    error_rate = max(0.1, random.gauss(0.3, 0.2) + 0.05 * hour_offset % 2.0)
                    rps = max(100, random.gauss(800, 200) + 10 * hour_offset % 1000)

                    base_dims = {
                        "region": region,
                        "service": service,
                        "dc": dc,
                        "env": env
                    }
                    tags = {"team": "infra", "critical": True}

                    data.extend([
                        {
                            "metric_name": "api_latency_p99",
                            "value": round(latency, 2),
                            "timestamp": ts,
                            "dimensions": base_dims,
                            "tags": tags,
                            "source": "synthetic"
                        },
                        {
                            "metric_name": "db_connections",
                            "value": int(db_conn),
                            "timestamp": ts,
                            "dimensions": base_dims,
                            "tags": tags,
                            "source": "synthetic"
                        },
                        {
                            "metric_name": "error_rate",
                            "value": round(error_rate, 2),
                            "timestamp": ts,
                            "dimensions": base_dims,
                            "tags": tags,
                            "source": "synthetic"
                        },
                        {
                            "metric_name": "rps",
                            "value": int(rps),
                            "timestamp": ts,
                            "dimensions": base_dims,
                            "tags": tags,
                            "source": "synthetic"
                        }
                    ])

    # Вставка
    if data:
        df = pd.DataFrame(data)
        # Сериализуем JSONB поля
        for col in ["dimensions", "tags"]:
            df[col] = df[col].apply(json.dumps)
        rows = df.to_dict(orient="records")
        inserted = bulk_insert_canonical_metrics(engine, rows)
        logger.info(f"✅ Вставлено {inserted} записей.")
    # Инвалидируем кэш ConfigService
    try:
        config_service = ConfigService()
        config_service.refresh()
        logger.info("🔁 Кэш ConfigService обновлён.")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось обновить кэш ConfigService: {mask_secrets(str(e))}")


# --- Главная функция ---
def main():
    parser = argparse.ArgumentParser(description="Генератор данных Situational Center v2")
    parser.add_argument("--init-db", action="store_true", help="Инициализировать схему БД")
    parser.add_argument("--init-metadata", action="store_true", help="Заполнить метаданные")
    parser.add_argument("--fill-sample", action="store_true", help="Заполнить синтетическими данными")
    parser.add_argument("--hours", type=int, default=24, help="Количество часов данных")

    args = parser.parse_args()

    # Логгирование
    settings.log_level = "INFO"
    logger.setLevel("INFO")

    # Подключение
    engine = get_engine()

    with global_lock("generate_data_init", timeout=30):
        if args.init_db:
            init_db_schema(engine)

        if args.init_metadata:
            insert_metadata(engine)

        if args.fill_sample:
            generate_sample_data(engine, hours=args.hours)

        init_ml_configs(engine)
        
    logger.info("✅ Генерация данных завершена.")


if __name__ == "__main__":
    main()