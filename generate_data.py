# generate_data.py
"""
Генератор тестовых данных и инициализатор метаданных для Situational Center v2.

Запуск:
    python generate_data.py --init-db --fill-sample --init-metadata
"""

import argparse
import glob
import os
import random
import pandas as pd
from datetime import datetime, timedelta, timezone
import json
from config import settings, logger, mask_secrets
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from core.database import get_engine
from core.locking import global_lock
import io


def bulk_insert_canonical_metrics(engine, records: list):
    if not records:
        return 0
    
    buf = io.StringIO()
    for r in records:
        metric_name = r.get("metric_name") or ""
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
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        conn.close()

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "migrations")


def init_db_schema(engine):
    """Применяет канонические SQL-миграции из db/migrations/.

    Это те же файлы, что монтируются в docker-entrypoint-initdb.d в проде, поэтому
    локальная схема (tenant_id, multi-tenancy, TimescaleDB, индексы, audit, SLA)
    полностью совпадает с продакшеном. Единый источник истины вместо устаревшего
    встроенного INIT_SCHEMA_SQL, который расходился со схемой прод-БД.
    """
    logger.info("🔧 Инициализация схемы БД из db/migrations/ ...")
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if not files:
        raise RuntimeError(f"Не найдено ни одной миграции в {MIGRATIONS_DIR}")

    raw = engine.raw_connection()
    dbapi = getattr(raw, "dbapi_connection", None) or getattr(raw, "connection", raw)
    try:
        # autocommit: применяем каждый файл как psql (нужно для CREATE EXTENSION /
        # create_hypertable, которые не работают внутри явной транзакции).
        dbapi.autocommit = True
        cur = dbapi.cursor()
        for path in files:
            name = os.path.basename(path)
            with open(path, "r", encoding="utf-8") as fh:
                sql = fh.read()
            if not sql.strip():
                continue
            try:
                cur.execute(sql)
                logger.info("  ✔ %s", name)
            except Exception as e:
                # Напр. 005_timescaledb.sql не применится на обычном PostgreSQL без
                # расширения timescaledb — для локальной разработки это нормально.
                logger.warning("  ⚠ %s пропущен: %s", name, mask_secrets(str(e)))
        cur.close()
    finally:
        try:
            dbapi.autocommit = False
        except Exception:
            pass
        raw.close()
    logger.info("✅ Схема БД инициализирована из db/migrations/.")


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
                ON CONFLICT (metric_name, tenant_id) DO UPDATE SET
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
                ON CONFLICT (dimension_key, tenant_id) DO UPDATE SET
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