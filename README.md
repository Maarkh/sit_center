# 📄 Проект "Ситуационный центр"

## 📝 Описание

Это веб-приложение для мониторинга различных метрик (сеть, логистика, ИТ, ИБ, жалобы) по регионам России. Данные визуализируются на интерактивной карте. Приложение автоматически обновляет данные и отправляет уведомления в Telegram при обнаружении аномалий.

## 🚀 Особенности

- Интерактивная карта с данными по регионам.
- Автоматическая ротация метрик.
- Возможность выбора метрики вручную.
- Уведомления в Telegram о критических значениях.
- Автоматическая генерация документации.
- CI/CD пайплайн для линтинга, тестирования и сборки Docker-образов.

## 🛠️ Установка

1. Клонируйте репозиторий.
2. Создайте виртуальное окружение: `python -m venv venv`
3. Активируйте виртуальное окружение:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
4. Установите зависимости: `pip install -r requirements.txt`
5. Создайте файл `.env`  и заполните его.
6. Создайте базу данных и сгенерируйте данные: `python generate_data.py`

## ▶️ Запуск



## 🧪 Тестирование

Запустите тесты с помощью `pytest`: `python -m pytest tests/ -v`

## 📁 Структура проекта

├── sit_center/
│   ├────── Dockerfile.celery
│   ├────── QUICKSTART.md
│   ├────── README.md
│   ├────── celery_app.py
│   ├────── celeryconfig.py
│   ├────── config.py
│   ├────── dlq_tool.py
│   ├────── docker-compose.ha.yml
│   ├────── docker-compose.prod.yml
│   ├────── docker-compose.test.yml
│   ├────── full_stack_architecture.txt
│   ├────── generate_data.py
│   ├────── generate_docs.py
│   ├────── init_schema.sql
│   ├────── instructions.md
│   ├────── kafka_consumer_main.py
│   ├────── requirements.txt
│   ├────── tasks.py
│   ├────── telegram_bot.py
│   ├────── wait-for-db-and-start.sh
│   ├── api/
│   │   ├────── Dockerfile.api
│   │   ├────── __init__.py
│   │   ├────── auth.py
│   │   ├────── dependencies.py
│   │   ├────── limiter.py
│   │   ├────── main.py
│   │   ├────── middleware.py
│   │   ├────── schemas.py
│   │   ├── __pycache__/
│   │   ├── routes/
│   │   │   ├────── __init__.py
│   │   │   ├────── admin.py
│   │   │   ├────── alerts.py
│   │   │   ├────── audit.py
│   │   │   ├────── auth.py
│   │   │   ├────── data.py
│   │   │   ├────── dimensions.py
│   │   │   ├────── forecasts.py
│   │   │   ├────── incidents.py
│   │   │   ├────── metrics.py
│   │   │   ├────── ml_configs.py
│   │   │   ├────── rules.py
│   │   │   ├────── webhooks.py
│   │   │   ├────── websocket.py
│   │   │   ├── __pycache__/
│   ├── .github/
│   │   ├── workflows/
│   │   │   ├────── ci-cd.yml
│   │   │   ├────── generate-docs.yml
│   ├── logs/
│   ├── __pycache__/
│   ├── db/
│   ├── nginx/
│   ├── docs/
│   │   ├────── disaster-recovery.md
│   ├── alembic/
│   │   ├────── env.py
│   │   ├── versions/
│   │   │   ├────── 001_add_admin_dashboard.py
│   │   │   ├────── 002_add_metadata_ml_configs.py
│   ├── k8s/
│   │   ├── sit-center/
│   │   │   ├────── Chart.yaml
│   │   │   ├────── values.yaml
│   │   │   ├── templates/
│   │   │   │   ├────── api-deployment.yaml
│   │   │   │   ├────── celery-deployment.yaml
│   │   │   │   ├────── hpa.yaml
│   │   │   │   ├────── ingress.yaml
│   │   │   │   ├────── ml-worker-deployment.yaml
│   │   │   │   ├────── service.yaml
│   ├── data/
│   ├── .claude/
│   ├── tests/
│   │   ├────── __init__.py
│   │   ├────── conftest.py
│   │   ├────── test_admin_api.py
│   │   ├────── test_alerts_logic.py
│   │   ├────── test_api_alerts.py
│   │   ├────── test_api_data.py
│   │   ├────── test_api_metrics.py
│   │   ├────── test_api_versioning.py
│   │   ├────── test_api_webhooks.py
│   │   ├────── test_audit_api.py
│   │   ├────── test_auth_oidc.py
│   │   ├────── test_auth_strategies.py
│   │   ├────── test_data_routes.py
│   │   ├────── test_dimensions_api.py
│   │   ├────── test_forecasts_api.py
│   │   ├────── test_idoit_service.py
│   │   ├────── test_incidents.py
│   │   ├────── test_mask_secrets.py
│   │   ├────── test_mask_secrets_edge.py
│   │   ├────── test_metadata_service.py
│   │   ├────── test_ml.py
│   │   ├────── test_ml_configs_api.py
│   │   ├────── test_ml_smoke.py
│   │   ├────── test_pubsub.py
│   │   ├────── test_rbac.py
│   │   ├────── test_resilience.py
│   │   ├────── test_rules_api.py
│   │   ├────── test_security.py
│   │   ├── __pycache__/
│   │   ├── load/
│   │   │   ├────── __init__.py
│   │   │   ├────── locustfile.py
│   │   │   ├── __pycache__/
│   │   ├── integration/
│   │   │   ├────── __init__.py
│   │   │   ├────── conftest.py
│   │   │   ├────── test_end_to_end.py
│   │   │   ├── __pycache__/
│   ├── .pytest_cache/
│   ├── documents/
│   ├── grafana/
│   │   ├── dashboards/
│   │   ├── provisioning/
│   │   │   ├── datasources/
│   │   │   │   ├────── postgres.yaml
│   │   │   ├── dashboards/
│   │   │   │   ├────── dashboard.yml
│   ├── .git/
│   │   ├── info/
│   │   ├── refs/
│   │   │   ├── remotes/
│   │   │   │   ├── origin/
│   │   │   ├── tags/
│   │   │   ├── heads/
│   │   ├── objects/
│   │   │   ├── 14/
│   │   │   ├── 5e/
│   │   │   ├── e1/
│   │   │   ├── 60/
│   │   │   ├── 77/
│   │   │   ├── info/
│   │   │   ├── fc/
│   │   │   ├── ac/
│   │   │   ├── 44/
│   │   │   ├── 42/
│   │   │   ├── 2a/
│   │   │   ├── 20/
│   │   │   ├── 21/
│   │   │   ├── ff/
│   │   │   ├── 4d/
│   │   │   ├── 7e/
│   │   │   ├── 4f/
│   │   │   ├── cb/
│   │   │   ├── 8e/
│   │   │   ├── 5d/
│   │   │   ├── 37/
│   │   │   ├── b9/
│   │   │   ├── 56/
│   │   │   ├── 90/
│   │   │   ├── 95/
│   │   │   ├── aa/
│   │   │   ├── 50/
│   │   │   ├── 1d/
│   │   │   ├── 7c/
│   │   │   ├── 1c/
│   │   │   ├── 38/
│   │   │   ├── 2f/
│   │   │   ├── 33/
│   │   │   ├── e7/
│   │   │   ├── a1/
│   │   │   ├── 0f/
│   │   │   ├── 7a/
│   │   │   ├── 19/
│   │   │   ├── 6d/
│   │   │   ├── de/
│   │   │   ├── a8/
│   │   │   ├── d4/
│   │   │   ├── 5f/
│   │   │   ├── c8/
│   │   │   ├── 7f/
│   │   │   ├── e5/
│   │   │   ├── 73/
│   │   │   ├── ed/
│   │   │   ├── 40/
│   │   │   ├── df/
│   │   │   ├── c7/
│   │   │   ├── 58/
│   │   │   ├── cf/
│   │   │   ├── 92/
│   │   │   ├── c6/
│   │   │   ├── 00/
│   │   │   ├── e6/
│   │   │   ├── a5/
│   │   │   ├── 1f/
│   │   │   ├── b3/
│   │   │   ├── 06/
│   │   │   ├── e0/
│   │   │   ├── f2/
│   │   │   ├── af/
│   │   │   ├── b7/
│   │   │   ├── e4/
│   │   │   ├── db/
│   │   │   ├── 9c/
│   │   │   ├── f5/
│   │   │   ├── 6e/
│   │   │   ├── 63/
│   │   │   ├── be/
│   │   │   ├── 87/
│   │   │   ├── b4/
│   │   │   ├── 48/
│   │   │   ├── 4e/
│   │   │   ├── ba/
│   │   │   ├── f0/
│   │   │   ├── 35/
│   │   │   ├── 83/
│   │   │   ├── c3/
│   │   │   ├── 84/
│   │   │   ├── 7b/
│   │   │   ├── 04/
│   │   │   ├── 99/
│   │   │   ├── ec/
│   │   │   ├── cc/
│   │   │   ├── 28/
│   │   │   ├── 4b/
│   │   │   ├── f8/
│   │   │   ├── 10/
│   │   │   ├── 3c/
│   │   │   ├── 34/
│   │   │   ├── 53/
│   │   │   ├── f6/
│   │   │   ├── 01/
│   │   │   ├── ea/
│   │   │   ├── 59/
│   │   │   ├── eb/
│   │   │   ├── b5/
│   │   │   ├── 0e/
│   │   │   ├── 24/
│   │   │   ├── 03/
│   │   │   ├── 18/
│   │   │   ├── 4a/
│   │   │   ├── 75/
│   │   │   ├── 8d/
│   │   │   ├── 0c/
│   │   │   ├── 79/
│   │   │   ├── 3a/
│   │   │   ├── d3/
│   │   │   ├── d0/
│   │   │   ├── 8f/
│   │   │   ├── fd/
│   │   │   ├── 47/
│   │   │   ├── 0b/
│   │   │   ├── 43/
│   │   │   ├── b8/
│   │   │   ├── 0a/
│   │   │   ├── 5c/
│   │   │   ├── bd/
│   │   │   ├── 12/
│   │   │   ├── 64/
│   │   │   ├── 8c/
│   │   │   ├── 51/
│   │   │   ├── 68/
│   │   │   ├── 27/
│   │   │   ├── 57/
│   │   │   ├── 98/
│   │   │   ├── a0/
│   │   │   ├── ca/
│   │   │   ├── 39/
│   │   │   ├── 86/
│   │   │   ├── a3/
│   │   │   ├── 9a/
│   │   │   ├── 55/
│   │   │   ├── 3e/
│   │   │   ├── 11/
│   │   │   ├── d2/
│   │   │   ├── 31/
│   │   │   ├── 61/
│   │   │   ├── 13/
│   │   │   ├── 9f/
│   │   │   ├── 7d/
│   │   │   ├── 05/
│   │   │   ├── b0/
│   │   │   ├── 74/
│   │   │   ├── c2/
│   │   │   ├── 9d/
│   │   │   ├── ce/
│   │   │   ├── 2d/
│   │   │   ├── 5a/
│   │   │   ├── 52/
│   │   │   ├── ae/
│   │   │   ├── d1/
│   │   │   ├── 62/
│   │   │   ├── dd/
│   │   │   ├── f7/
│   │   │   ├── 54/
│   │   │   ├── fa/
│   │   │   ├── 67/
│   │   │   ├── 17/
│   │   │   ├── 6c/
│   │   │   ├── pack/
│   │   │   ├── ab/
│   │   │   ├── b1/
│   │   │   ├── 5b/
│   │   │   ├── 76/
│   │   │   ├── d7/
│   │   │   ├── bb/
│   │   │   ├── 71/
│   │   │   ├── 6f/
│   │   │   ├── c5/
│   │   │   ├── 2b/
│   │   │   ├── a2/
│   │   │   ├── 26/
│   │   │   ├── 88/
│   │   │   ├── 9e/
│   │   │   ├── 25/
│   │   ├── logs/
│   │   ├── hooks/
│   ├── core/
│   │   ├────── __init__.py
│   │   ├────── alert_settings.py
│   │   ├────── alerts.py
│   │   ├────── analytics_service.py
│   │   ├────── audit.py
│   │   ├────── auth_strategies.py
│   │   ├────── celery_metrics.py
│   │   ├────── clickhouse.py
│   │   ├────── config_service.py
│   │   ├────── data.py
│   │   ├────── database.py
│   │   ├────── exceptions.py
│   │   ├────── idoit_service.py
│   │   ├────── kafka_consumer.py
│   │   ├────── kafka_producer.py
│   │   ├────── ldap_auth.py
│   │   ├────── locking.py
│   │   ├────── metadata_service.py
│   │   ├────── metric_service.py
│   │   ├────── ml_anomaly.py
│   │   ├────── ml_tasks.py
│   │   ├────── models.py
│   │   ├────── notifications.py
│   │   ├────── oidc_auth.py
│   │   ├────── pubsub.py
│   │   ├────── rbac.py
│   │   ├────── resilience.py
│   │   ├────── rule_engine.py
│   │   ├────── sla_service.py
│   │   ├────── smart_alerts.py
│   │   ├────── tenant.py
│   │   ├────── tracing.py
│   │   ├────── utils.py
│   │   ├────── vault.py
│   │   ├── __pycache__/
## 💻 Коды основных модулей
### 📄 `Dockerfile.celery`

```
# Dockerfile.celery
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Убедимся, что файлы исполняемы
RUN chmod +x wait-for-db-and-start.sh

# Переменные окружения (временные, переопределятся в docker-compose)
ENV PYTHONPATH=/app

# Команда по умолчанию — будет переопределена в docker-compose
CMD ["celery", "-A", "tasks.celery_app", "worker", "-l", "INFO", "--concurrency", "2"]
```
### 📄 `QUICKSTART.md`

```markdown
# Quick Start Guide

Minimal setup for local development. Full stack requires ~2GB RAM.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## 1. Clone & Setup

```bash
git clone <repo-url> sit_center && cd sit_center
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Environment

```bash
cp env.example .env
# Edit .env — minimum required:
#   POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB
#   REDIS_HOST, REDIS_PORT
#   SECRET_KEY (any random string)
#   ADMIN_USERNAME, ADMIN_PASSWORD (bcrypt hash)
#   I_DOIT_API_KEY, I_DOIT_API_URL (can be placeholder)
#   WEBHOOK_API_KEY (any string)
```

## 3. Start Infrastructure (minimal)

```bash
# Only PostgreSQL + Redis — enough for API development
docker compose -f docker-compose.prod.yml up -d db redis
```

Wait for healthy status:
```bash
docker compose -f docker-compose.prod.yml ps
```

## 4. Apply Migrations

```bash
alembic upgrade head
```

## 5. Run API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

## 6. Run Tests

```bash
TESTING=1 python -m pytest tests/ --ignore=tests/test_ml.py -v
```

## Optional Components

Each component is independently toggleable via environment variables:

| Component | Enable | Start Command |
|-----------|--------|---------------|
| Celery Worker | always on | `celery -A tasks.celery_app worker -l INFO` |
| Celery Beat | always on | `celery -A tasks.celery_app beat -l INFO` |
| ML Worker | `ML_METHODS` env | `celery -A celery_app worker -Q ml -l INFO --concurrency=1` |
| Kafka | `KAFKA_ENABLED=true` | `docker compose up -d zookeeper kafka kafka-consumer` |
| ClickHouse | `CLICKHOUSE_ENABLED=true` | `docker compose up -d clickhouse` |
| Grafana | always available | `docker compose up -d grafana` (http://localhost:3000) |
| Keycloak SSO | `OIDC_ENABLED=true` | `docker compose up -d keycloak-db keycloak` |
| i-doit (ITSM) | standalone | `docker compose up -d idoit-db idoit` (http://localhost:9080) |
| Flower | standalone | `docker compose up -d flower` (http://localhost:5555) |

## Full Stack

```bash
docker compose -f docker-compose.prod.yml up -d
```

This starts all 17 services. Requires ~8GB RAM.

## Architecture Overview

```
Client -> FastAPI (port 8000) -> PostgreSQL/TimescaleDB
                              -> Redis (cache + pubsub)
                              -> Celery (background tasks)
                              -> ML Worker (anomaly detection)
                              -> Kafka (optional, streaming)
                              -> ClickHouse (optional, OLAP)
```

## Troubleshooting

**Redis connection refused**: Ensure Redis is running (`docker compose up -d redis`)

**Database not found**: Run `alembic upgrade head` to create tables

**ML tests fail**: ML tests require `prophet`, `tensorflow`, `torch` — skip with `--ignore=tests/test_ml.py`

**Rate limiting errors in tests**: Set `TESTING=1` environment variable

```
### 📄 `celery_app.py`

```python
# celery_app.py
from __future__ import annotations
from celery import Celery
from urllib.parse import quote_plus
from celery.signals import worker_shutting_down


def make_celery(app_name=__name__):
    from config import settings, logger

    if settings.REDIS_URL:
        redis_url = settings.REDIS_URL
    else:
        pwd = quote_plus(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ""
        redis_url = f"redis://:{pwd}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        broker_connection_retry_on_startup=True,
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        beat_schedule=get_beat_schedule(),
        task_routes={
            'core.ml_tasks.*': {'queue': 'ml'},
        },
    )
    return celery

def get_beat_schedule():
    from celeryconfig import beat_schedule
    return beat_schedule

celery_app = make_celery()

import core.celery_metrics  # noqa: F401, E402 — register Celery signal handlers

@worker_shutting_down.connect
def worker_shutting_down_handler(sig, how, exitcode, **kwargs):
    from config import logger
    logger.info(f"Worker shutting down (sig={sig}, how={how})")


```
### 📄 `celeryconfig.py`

```python
# 📄 celeryconfig.py (новый файл)
from celery.schedules import crontab

beat_schedule = {
    'ml-anomaly-10min': {
        'task': 'core.ml_tasks.run_ml_anomaly_check',
        'schedule': crontab(minute='*/10')
    },
    'retrain-ml-models-daily': {
        'task': 'core.ml_tasks.retrain_ml_models',
        'schedule': crontab(hour=3, minute=0)
    },
    'update-mv-10min': {
        'task': 'tasks.update_mv_data',
        'schedule': crontab(minute='*/10')
    },
    'evaluate-rules-1min': {
        'task': 'core.ml_tasks.evaluate_rules_task',
        'schedule': crontab(minute='*/1')
    },
    'check-sla-breaches-5min': {
        'task': 'tasks.check_sla_breaches_task',
        'schedule': crontab(minute='*/5')
    },
    'check-auto-escalation-5min': {
        'task': 'tasks.check_auto_escalation_task',
        'schedule': crontab(minute='*/5')
    },
}
```
### 📄 `config.py`

```python
# config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict
from pydantic import Field, PostgresDsn
import logging
import logging.handlers
import redis
import json
import os
import re
import threading

# Создаём базовый логгер сразу
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sit_center")

PROJECT_ROOT = Path(__file__).parent

def mask_secrets(s: str) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)

    # Redis/Postgres URLs: mask password between : and @
    s = re.sub(r"(redis://[^:@]*:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)
    s = re.sub(r"(postgres(?:ql)?://[^:@]*:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)

    # Telegram bot token: bot<id>:<token> -> bot<id>:***
    s = re.sub(r"(bot\d+:)[A-Za-z0-9_\-]+", r"\1***", s, flags=re.IGNORECASE)

    # JSON keys like "password": "xxx" -> mask value
    s = re.sub(
        r'(["\'])(password|token|secret|key|pwd|pass)(["\']\s*:\s*["\'])([^"\']+)(["\'])',
        r'\1\2\3***\5',
        s,
        flags=re.IGNORECASE
    )

    # Generic key=value pairs
    s = re.sub(r'\b(password|pwd|secret|token)=\S+', r'\1=***', s, flags=re.IGNORECASE)

    return s

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_secrets(record.getMessage()),
        }
        if record.exc_info:
            # Маскируем traceback тоже
            tb = self.formatException(record.exc_info)
            log_entry["exception"] = mask_secrets(tb)
        return json.dumps(log_entry, ensure_ascii=False)

class Settings(BaseSettings):
    # --- Подключение к БД ---
    DATABASE_URL: Optional[PostgresDsn] = Field(None, env="DATABASE_URL") # type: ignore
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER") # type: ignore
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD") # type: ignore
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER") # type: ignore
    POSTGRES_PORT: int = Field(..., env="POSTGRES_PORT") # type: ignore
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB") # type: ignore

    # --- Redis ---
    REDIS_HOST: str = Field(..., env="REDIS_HOST") # type: ignore
    REDIS_PORT: int = Field(..., env="REDIS_PORT") # type: ignore
    REDIS_DB: int = Field(0, env="REDIS_DB") # type: ignore
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD") # type: ignore
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL") # type: ignore

    # --- Пути ---
    data_regions_path: Path = PROJECT_ROOT / "data" / "regions.csv"
    geojson_path: Path = PROJECT_ROOT / "data" / "russia.geojson"
    static_folder: Path = PROJECT_ROOT / "static"
    log_dir: Path = PROJECT_ROOT / "logs"

    # --- Аудио ---
    audio_file_path: str = "alert.mp3"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN") # type: ignore
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID") # type: ignore
    TELEGRAM_CHAT_ID_WARNING: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID_WARNING") # type: ignore
    TELEGRAM_CHAT_ID_CRITICAL: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID_CRITICAL") # type: ignore

    # --- Кэширование ---
    cache_ttl: int = 30  # секунд
    smart_alert_cache_ttl: int = 300  # 5 минут
    cache_locking_timeout: int = 30  # seconds
    cache_poll_interval: float = 0.1  # seconds

    # --- Логирование ---
    log_level: str = "INFO"
    
    # ML настройки
    ml_model_cache_days: int = Field(7, env="ML_MODEL_CACHE_DAYS") # type: ignore
    ml_retrain_hour: int = Field(3, env="ML_RETRAIN_HOUR") # type: ignore
    ml_methods: List[str] = Field(["prophet", "lstm", "clustering"], env="ML_METHODS") # type: ignore
    ML_MAX_WORKERS: int = Field(4, env="ML_MAX_WORKERS")  # type: ignore # Количество параллельных воркеров

    # --- Ключи кэша ---
    GEOJSON_CACHE_KEY: str = "geojson_data"
    DASHBOARD_CACHE_KEY: str = "custom_dashboard_metrics"

    # --- Прочее ---
    secret_key: str = Field(..., env="SECRET_KEY") # type: ignore
    alert_cooldown: int = 3600  # секунд
    
    I_DOIT_API_KEY: str = Field(..., env="I_DOIT_API_KEY") # type: ignore
    I_DOIT_API_URL: str = Field(..., env="I_DOIT_API_URL") # type: ignore
    ADMIN_USERNAME: str = Field(..., env="ADMIN_USERNAME") # type: ignore
    ADMIN_PASSWORD: str = Field(..., env="ADMIN_PASSWORD")     # type: ignore
    WEBHOOK_API_KEY: str = Field(..., env="WEBHOOK_API_KEY") # type: ignore

    # --- Kafka ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS") # type: ignore
    KAFKA_ENABLED: bool = Field(False, env="KAFKA_ENABLED") # type: ignore

    # --- ClickHouse ---
    CLICKHOUSE_HOST: str = Field("clickhouse", env="CLICKHOUSE_HOST") # type: ignore
    CLICKHOUSE_PORT: int = Field(8123, env="CLICKHOUSE_PORT") # type: ignore
    CLICKHOUSE_USER: str = Field("default", env="CLICKHOUSE_USER") # type: ignore
    CLICKHOUSE_PASSWORD: str = Field("", env="CLICKHOUSE_PASSWORD") # type: ignore
    CLICKHOUSE_DB: str = Field("sit_center", env="CLICKHOUSE_DB") # type: ignore
    CLICKHOUSE_ENABLED: bool = Field(False, env="CLICKHOUSE_ENABLED") # type: ignore

    # --- LDAP ---
    LDAP_ENABLED: bool = Field(False, env="LDAP_ENABLED") # type: ignore
    LDAP_URL: str = Field("ldap://localhost:389", env="LDAP_URL") # type: ignore
    LDAP_BASE_DN: str = Field("", env="LDAP_BASE_DN") # type: ignore
    LDAP_BIND_DN: str = Field("", env="LDAP_BIND_DN") # type: ignore
    LDAP_BIND_PASSWORD: str = Field("", env="LDAP_BIND_PASSWORD") # type: ignore
    LDAP_USER_SEARCH_FILTER: str = Field("(sAMAccountName={username})", env="LDAP_USER_SEARCH_FILTER") # type: ignore
    LDAP_GROUP_ROLE_MAP: Dict[str, str] = Field(default_factory=dict, env="LDAP_GROUP_ROLE_MAP") # type: ignore

    # --- OIDC (Keycloak SSO) ---
    OIDC_ENABLED: bool = Field(False, env="OIDC_ENABLED") # type: ignore
    OIDC_ISSUER_URL: str = Field("", env="OIDC_ISSUER_URL") # type: ignore
    OIDC_CLIENT_ID: str = Field("", env="OIDC_CLIENT_ID") # type: ignore
    OIDC_CLIENT_SECRET: str = Field("", env="OIDC_CLIENT_SECRET") # type: ignore
    OIDC_BASE_URL: str = Field("http://localhost:8000", env="OIDC_BASE_URL") # type: ignore

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        "http://localhost:8050,http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS",
    ) # type: ignore

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорируем неизвестные поля


# Inject Vault secrets into env before Settings init (if VAULT_ENABLED=true)
try:
    from core.vault import inject_vault_secrets
    inject_vault_secrets()
except Exception:
    pass

settings = Settings() # type: ignore


# === Глобальные объекты ===

# 🟡 Redis-клиент (ленивая инициализация)
_redis_client = None
_redis_lock = threading.Lock()


def get_redis():
    global _redis_client
    
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            # Соединение потеряно, закрываем старый клиент
            try:
                _redis_client.close()
            except Exception:
                pass
            _redis_client = None
    
    with _redis_lock:
        # Double-check после получения блокировки
        if _redis_client is not None:
            return _redis_client
            
        try:
            if settings.REDIS_URL:
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                _redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            _redis_client.ping()
            logger.info("✅ Подключено к Redis")
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к Redis: {mask_secrets(str(e))}")
            raise
    
    return _redis_client


def close_redis():
    global _redis_client
    with _redis_lock:
        if _redis_client is not None:
            try:
                _redis_client.connection_pool.disconnect()
            except Exception:
                pass
            _redis_client = None

def get_cache():
    """Возвращает Redis-клиент как кэш"""
    return get_redis()


def get_database_url() -> str:
    """Формирует URL для подключения к PostgreSQL"""
    if settings.DATABASE_URL:
        return str(settings.DATABASE_URL)
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


def setup_logging():
    """Инициализация логирования (вызывать после monkey_patch)"""
    global logger
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    settings.log_dir.mkdir(exist_ok=True)
    
    if os.getenv("LOG_JSON", "false").lower() == "true":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"⚠️ Не удалось создать файл лога: {e}")

    logger.setLevel(settings.log_level.upper())
    logger.info("✅ Логирование инициализировано")
    
def init_app_logging():
    global logger
    try:
        # settings уже инициализирован (Settings())
        logger.handlers.clear()
        logger.setLevel(settings.log_level.upper())
        setup_logging()
    except Exception as e:
        # безопасный fallback
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning(f"Не удалось полностью инициализировать логирование: {e}")
```
### 📄 `dlq_tool.py`

```python
# dlq_tool.py
from tasks import send_notification
from config import get_redis


def replay_dlq():
    r = get_redis()
    entries = r.xrange("dlq:notifications", count=10)
    for _id, fields in entries: # type: ignore
        # Если client был с decode_responses=True — поля уже str; иначе bytes
        def _get(field_name):
            v = fields.get(field_name)
            if isinstance(v, bytes):
                return v.decode()
            return v

        msg = _get("message") or ""
        priority = _get("priority") or "info"
        send_notification.delay(msg, priority) # type: ignore
        r.xdel("dlq:notifications", _id)
        print(f"🔁 Повтор: {msg[:80]}...")
```
### 📄 `docker-compose.ha.yml`

```yaml
# docker-compose.ha.yml
# High-Availability override: run with
#   docker-compose -f docker-compose.prod.yml -f docker-compose.ha.yml up -d

services:
  # --- API instances behind nginx ---
  api-1:
    extends:
      file: docker-compose.prod.yml
      service: api
    ports: []   # nginx will proxy
    container_name: api-1

  api-2:
    extends:
      file: docker-compose.prod.yml
      service: api
    ports: []
    container_name: api-2

  # --- Nginx Load Balancer ---
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "8000:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-1
      - api-2
    networks:
      - app-network
    restart: unless-stopped

  # --- Redis Sentinel (3 nodes) ---
  redis-sentinel-1:
    image: redis:7-alpine
    command: >
      sh -c "cat > /etc/redis/sentinel.conf << 'EOF'
      port 26379
      sentinel monitor mymaster redis 6379 2
      sentinel down-after-milliseconds mymaster 5000
      sentinel failover-timeout mymaster 10000
      sentinel parallel-syncs mymaster 1
      EOF
      redis-sentinel /etc/redis/sentinel.conf"
    networks:
      - app-network
    restart: unless-stopped

  redis-sentinel-2:
    image: redis:7-alpine
    command: >
      sh -c "cat > /etc/redis/sentinel.conf << 'EOF'
      port 26379
      sentinel monitor mymaster redis 6379 2
      sentinel down-after-milliseconds mymaster 5000
      sentinel failover-timeout mymaster 10000
      sentinel parallel-syncs mymaster 1
      EOF
      redis-sentinel /etc/redis/sentinel.conf"
    networks:
      - app-network
    restart: unless-stopped

  redis-sentinel-3:
    image: redis:7-alpine
    command: >
      sh -c "cat > /etc/redis/sentinel.conf << 'EOF'
      port 26379
      sentinel monitor mymaster redis 6379 2
      sentinel down-after-milliseconds mymaster 5000
      sentinel failover-timeout mymaster 10000
      sentinel parallel-syncs mymaster 1
      EOF
      redis-sentinel /etc/redis/sentinel.conf"
    networks:
      - app-network
    restart: unless-stopped

  # --- DB Replica (streaming replication) ---
  db-replica:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    command: >
      bash -c "
        until pg_isready -h db -U $${POSTGRES_USER}; do sleep 2; done;
        pg_basebackup -h db -U $${POSTGRES_USER} -D /var/lib/postgresql/data -Fp -Xs -P -R;
        postgres
      "
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_replica_data:

networks:
  app-network:
    driver: bridge

```
### 📄 `docker-compose.prod.yml`

```yaml
services:
  # ——— PostgreSQL для Situational Center ———
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d  # ← Только для основной БД
    ports:
      - "5433:5432"
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ——— Redis ———
  redis:
    image: redis:7-alpine
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}"]
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ——— Airbyte: PostgreSQL (только для Airbyte) ———
  airbyte-db:
    image: postgres:13
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: airbyte
    volumes:
      - airbyte_db_data:/var/lib/postgresql/data
      # ❌ УДАЛЕНО: ./db/migrations — Airbyte сам управляет своей схемой
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ——— Airbyte: Temporal ———
  airbyte-temporal:
    image: airbyte/temporal:${AIRBYTE_VERSION:-0.50.4}
    environment:
      - DB=postgresql
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_SEEDS=airbyte-db
      - POSTGRES_DB=airbyte
    depends_on:
      airbyte-db:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  # ——— Airbyte: Server ———
  airbyte-server:
    image: airbyte/server:${AIRBYTE_VERSION:-0.50.4}
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@airbyte-db:5432/airbyte
      - CONFIG_DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@airbyte-db:5432/airbyte
      - TEMPORAL_HOST=airbyte-temporal
      - WORKSPACE_ROOT=/tmp/workspace
      - LOCAL_ROOT=/tmp/workspace
      - LOG_LEVEL=INFO
    depends_on:
      airbyte-db:
        condition: service_healthy
      airbyte-temporal:
        condition: service_started
    volumes:
      - airbyte_workspace:/tmp/workspace
    networks:
      - app-network
    restart: unless-stopped

  # ——— Airbyte: Worker ———
  airbyte-worker:
    image: airbyte/worker:${AIRBYTE_VERSION:-0.50.4}
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@airbyte-db:5432/airbyte
      - TEMPORAL_HOST=airbyte-temporal
      - WORKSPACE_ROOT=/tmp/workspace
      - LOCAL_ROOT=/tmp/workspace
      - WORKER_ENVIRONMENT=docker
    depends_on:
      airbyte-db:
        condition: service_healthy
      airbyte-temporal:
        condition: service_started
    volumes:
      - airbyte_workspace:/tmp/workspace
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - app-network
    restart: unless-stopped

  # ——— Airbyte: Web UI ———
  airbyte-webapp:
    image: airbyte/webapp:${AIRBYTE_VERSION:-0.50.4}
    ports:
      - "8001:80"
    environment:
      - API_URL=http://airbyte-server:8001
    depends_on:
      - airbyte-server
    networks:
      - app-network
    restart: unless-stopped

  # ——— FastAPI ———
  api:
    build:
      context: .
      dockerfile: api/Dockerfile.api
    image: situational-center/api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - TELEGRAM_CHAT_ID_CRITICAL=${TELEGRAM_CHAT_ID_CRITICAL}
      - TELEGRAM_CHAT_ID_WARNING=${TELEGRAM_CHAT_ID_WARNING}
      - I_DOIT_API_URL=${I_DOIT_API_URL}
      - I_DOIT_API_KEY=${I_DOIT_API_KEY}
      - WEBHOOK_API_KEY=${WEBHOOK_API_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  # ——— Grafana ———
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # ——— Celery Worker ———
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: >
      celery -A tasks.celery_app worker
      --loglevel=INFO
      --concurrency=2
      --max-tasks-per-child=100
      --pool=prefork
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "celery", "call", "tasks.healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  # ——— ML Worker (dedicated queue) ———
  ml-worker:
    build:
      context: .
      dockerfile: Dockerfile.ml-worker
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 4G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "celery", "-A", "celery_app", "inspect", "ping", "-d", "celery@$$HOSTNAME"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # ——— Celery Beat ———
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: ["celery", "-A", "tasks.celery_app", "beat", "-l", "INFO", "--scheduler", "celery.beat:PersistentScheduler"]
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "celery", "call", "tasks.healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ——— Flower (Celery monitor) ———
  flower:
    image: mher/flower
    command: ["celery", "--broker=redis://:${REDIS_PASSWORD}@redis:6379/0", "flower", "--port=5555"]
    ports:
      - "5555:5555"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5555/healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ——— ClickHouse (OLAP analytics) ———
  clickhouse:
    image: clickhouse/clickhouse-server:23.8
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./db/clickhouse/init_schema.sql:/docker-entrypoint-initdb.d/init_schema.sql
    environment:
      CLICKHOUSE_DB: sit_center
      CLICKHOUSE_USER: default
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 15s
      timeout: 5s
      retries: 5

  # ——— Zookeeper (for Kafka) ———
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "echo ruok | nc localhost 2181 | grep imok"]
      interval: 15s
      timeout: 5s
      retries: 5

  # ——— Kafka ———
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      zookeeper:
        condition: service_healthy
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1"]
      interval: 20s
      timeout: 10s
      retries: 5
      start_period: 30s

  # ——— Kafka Consumer ———
  kafka-consumer:
    build:
      context: .
      dockerfile: Dockerfile.kafka-consumer
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_ENABLED=true
    depends_on:
      db:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "python3 -c 'import kafka; print(\"ok\")' 2>/dev/null || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # ——— i-doit (ITSM / CMDB) ———
  idoit-db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${IDOIT_DB_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: ${IDOIT_DB_NAME:-idoit}
      MYSQL_USER: ${IDOIT_DB_USER:-idoit}
      MYSQL_PASSWORD: ${IDOIT_DB_PASS:-idoit}
    volumes:
      - idoit_mysql_data:/var/lib/mysql
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 10

  idoit:
    image: bheisig/idoit:1.19
    environment:
      IDOIT_DB_HOST: idoit-db
      IDOIT_DB_NAME: ${IDOIT_DB_NAME:-idoit}
      IDOIT_DB_USERNAME: ${IDOIT_DB_USER:-idoit}
      IDOIT_DB_PASSWORD: ${IDOIT_DB_PASS:-idoit}
      IDOIT_DB_ROOT_PASSWORD: ${IDOIT_DB_ROOT_PASSWORD:-root}
      IDOIT_ADMIN_PASSWORD: ${IDOIT_ADMIN_PASS:-admin}
      IDOIT_DEFAULT_TENANT: sit-center
    ports:
      - "9080:80"
    depends_on:
      idoit-db:
        condition: service_healthy
    volumes:
      - idoit_data:/var/www/html
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

  # ——— Keycloak DB ———
  keycloak-db:
    image: postgres:15
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: ${KEYCLOAK_DB_PASSWORD:-keycloak}
    volumes:
      - keycloak_db_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keycloak"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ——— Keycloak (OIDC SSO) ———
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    command: start-dev
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD:-keycloak}
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN:-admin}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-admin}
      KC_HEALTH_ENABLED: "true"
    ports:
      - "8443:8080"
    depends_on:
      keycloak-db:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/localhost/8080 && echo -e 'GET /health/ready HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n' >&3 && cat <&3 | grep -q '200'"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  airbyte_db_data:
  airbyte_workspace:
  idoit_mysql_data:
  idoit_data:
  keycloak_db_data:
  clickhouse_data:
  zookeeper_data:
  kafka_data:
```
### 📄 `docker-compose.test.yml`

```yaml
services:
  test-db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
      POSTGRES_DB: test_db
    ports:
      - "5444:5432"
    volumes:
      - ./db/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user"]
      interval: 5s
      timeout: 3s
      retries: 10

  test-redis:
    image: redis:7-alpine
    ports:
      - "6399:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

```
### 📄 `full_stack_architecture.txt`

```
     ┌──────────────┐
     │  Источники   │ ← Kafka, API, CSV, DB, Prometheus, Logs, etc.
     └──────┬───────┘
            ↓
     ┌──────────────┐
     │   Airbyte    │ → EL(T) → staging
     └──────┬───────┘
            ↓
     ┌───────────────────────────────────────────────────────┐
     │  Data Lake / PostgreSQL (staging + canonical)        │
     │   - raw_*: как есть из источника                     │
     │   - canonical_metrics:                               │
     │        metric_name TEXT     ← user-defined           │
     │        value       NUMERIC  ← always float/decimal   │
     │        timestamp   TIMESTAMPTZ                       │
     │        dimensions  JSONB    ← {"region": "RU", "team": "ops"} │
     │        tags        JSONB    ← {"env": "prod", "critical": true} │
     └──────┬───────────────────────────────────────────────┘
            ↓
     ┌──────────────────────┐
     │   Metadata Service   │ ← где живёт знание:
     │                      │   - какие метрики активны
     │                      │   - какие dimensions есть
     │                      │   - как агрегировать
     │                      │   - по каким правилам мониторить
     └──────┬───────────────┘
            ↓
     ┌──────────────────────────────────────────────┐
     │   Rule Engine + Alert Manager (GoAlert-style)│
     │      - condition: Prometheus-like expr       │
     │      - eval:  every: 1m, for: 3m             │
     │      - actions: [ telegram, webhook, incident ] │
     │      - labels: { severity: "critical" }      │
     └──────┬───────────────────────────────────────┘
            ↓
     ┌───────────────────────────────────────────────────────────┐
     │  ML Service (per config)                                  │
     │    Пользователь создаёт ML-задачу:                         │
     │      - metric_name: "error_rate"                          │
     │      - group_by: ["service", "dc"]                        │
     │      - method: ["prophet", "lstm"]                        │
     │      - retrain_schedule: "0 3 * * *"                      │
     │    → модель обучается на `canonical_metrics WHERE …`     │
     │    → аномалии → запись в `ml_anomalies` + лейбл `ml:true`│
     └──────┬───────────────────────────────────────────────────┘
            ↓
     ┌────────────────────────────────────────┐
     │          Grafana (UI/UX)               │
     │   - Dashboards as Code (Grafonnet)     │
     │   - Variables: $__metric, $__dimension │
     │   - Panel per metric/group             │
     │   - Alert history + incidents          │
     └──────┬─────────────────────────────────┘
            ↓
     ┌────────────────────────────────────────────────────────┐
     │  Notification Receiver + Webhook Gateway              │
     │    (тот же `webhook_receiver.py`, но с поддержкой:     │
     │      - динамических action handlers                     │
     │      - idempotency keys                                  │
     │      - retry policies                                    │
     └────────────────────────────────────────────────────────┘

```
### 📄 `generate_data.py`

```python
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
```
### 📄 `generate_docs.py`

```python
# generate_docs.py
import os
import re
from pathlib import Path
import pathspec
from datetime import datetime
from docx import Document
from docx.shared import Pt

PROJECT_ROOT = Path(__file__).parent
README_FILE = PROJECT_ROOT / "README.md"
DOCS_DIR = PROJECT_ROOT / "documents"

EXTRA_FILES_WITHOUT_EXTENSION = {
    "Dockerfile", "Dockerfile.cpu", "Dockerfile.gpu", "Makefile", ".dockerignore", "LICENSE"
}
INCLUDED_EXTENSIONS = [".py", ".yaml", ".env", ".txt", ".md", ".yml", ".toml", ".sh",'.sql','.api','.webhook','.idoit_webhook','.celery']

EXCLUDED_FILES = {
    ".env", "secrets.py", "config_local.py", "id_rsa", "id_rsa.pub",
    "known_hosts", "docker-compose.override.yml", "token.txt"
}

SYNTAX_HIGHLIGHTING_MAP = {
    ".py": "python",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "bash",
    ".env": "env",
    ".txt": "",
    ".md": "markdown",
    ".csv": "",
    ".xlsx": "",
    ".json": "json",
    "Dockerfile": "Dockerfile",
    "Makefile": "makefile"
}

# Используем "сырую" строку (r""") или экранируем \
# Также обновим заголовок для лучшего описания
README_HEADER = r"""# 📄 Проект "Ситуационный центр"

## 📝 Описание

Это веб-приложение для мониторинга различных метрик (сеть, логистика, ИТ, ИБ, жалобы) по регионам России. Данные визуализируются на интерактивной карте. Приложение автоматически обновляет данные и отправляет уведомления в Telegram при обнаружении аномалий.

## 🚀 Особенности

- Интерактивная карта с данными по регионам.
- Автоматическая ротация метрик.
- Возможность выбора метрики вручную.
- Уведомления в Telegram о критических значениях.
- Автоматическая генерация документации.
- CI/CD пайплайн для линтинга, тестирования и сборки Docker-образов.

## 🛠️ Установка

1. Клонируйте репозиторий.
2. Создайте виртуальное окружение: `python -m venv venv`
3. Активируйте виртуальное окружение:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
4. Установите зависимости: `pip install -r requirements.txt`
5. Создайте файл `.env`  и заполните его.
6. Создайте базу данных и сгенерируйте данные: `python generate_data.py`

## ▶️ Запуск



## 🧪 Тестирование

Запустите тесты с помощью `pytest`: `python -m pytest tests/ -v`

## 📁 Структура проекта
""" # Конец строки README_HEADER

def load_gitignore_spec():
    gitignore_path = PROJECT_ROOT / ".gitignore"
    if not gitignore_path.exists():
        return None
    with open(gitignore_path, "r", encoding="utf-8") as f:
        spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
    return spec

def should_include(path, spec):
    rel_path = path.relative_to(PROJECT_ROOT)
    if path.name in EXCLUDED_FILES:
        return False
    return spec is None or not spec.match_file(rel_path)

def generate_tree(start_path, spec):
    tree = []
    for root, dirs, files in os.walk(start_path):
        filtered_dirs = [d for d in dirs if should_include(Path(root) / d, spec)]
        dirs[:] = filtered_dirs
        level = root.replace(str(start_path), "").count(os.sep)
        indent = "│   " * level
        dir_name = os.path.basename(root)
        if level == 0:
            tree.append(f"├── {dir_name}/")
        else:
            tree.append(f"{indent}├── {dir_name}/")
        subindent = "│   " * (level + 1)
        for f in sorted(files):
            full_path = Path(root) / f
            if should_include(full_path, spec):
                if f in EXTRA_FILES_WITHOUT_EXTENSION:
                    tree.append(f"{subindent}├────── {f}")
                elif any(f.endswith(ext) for ext in INCLUDED_EXTENSIONS):
                    tree.append(f"{subindent}├────── {f}")
    return "\n".join(tree).replace("├────── └──", "└──────").replace("├── └──", "└──")

def read_file_content(file_path):
    file_name = file_path.name
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if file_name in SYNTAX_HIGHLIGHTING_MAP:
            lang = SYNTAX_HIGHLIGHTING_MAP[file_name]
        else:
            lang = SYNTAX_HIGHLIGHTING_MAP.get(file_path.suffix, "")
        return f"```{lang}\n{content}\n```"
    except Exception as e:
        return f"<!-- Ошибка чтения файла: {e} -->\n\n"

def gather_files(start_path, spec):
    file_contents = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if should_include(Path(root) / d, spec)]
        for f in sorted(files):
            if f == "README.md":
                continue
            full_path = Path(root) / f
            if should_include(full_path, spec):
                if f in EXTRA_FILES_WITHOUT_EXTENSION or any(f.endswith(ext) for ext in INCLUDED_EXTENSIONS):
                    rel_path = full_path.relative_to(PROJECT_ROOT)
                    file_contents.append(f"### 📄 `{rel_path}`\n")
                    file_contents.append(read_file_content(full_path))
    return "\n".join(file_contents)

# --- Новая функция для очистки текста ---
def clean_text_for_xml(text: str) -> str:
    """
    Убираем недопустимые символы для XML 1.0.
    Разрешаем: \t (0x09), \n (0x0A), \r (0x0D) и U+0020..U+D7FF, U+E000..U+FFFD, U+10000..U+10FFFF
    """
    if not isinstance(text, str):
        text = str(text)

    # Удаляем управляющие символы U+0000 - U+001F, кроме таб(9), lf(10), cr(13)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    # Удаляем non-characters U+FFFE, U+FFFF and their high-plane equivalents
    text = re.sub(r'[\uFFFE\uFFFF]', '', text)
    # Также принудительно заменить суррогатные пары, если они появились (условный safe)
    # При кодировке/декодировании с 'utf-8' и errors='ignore' мы убираем невалидные суррогаты
    try:
        text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        # В крайнем случае — убираем всё не-ASCII печатное
        text = ''.join(ch for ch in text if ord(ch) >= 32)

    return text

def build_documentation():
    spec = load_gitignore_spec()
    structure = generate_tree(PROJECT_ROOT, spec)
    code_sections = gather_files(PROJECT_ROOT, spec)
    
    # Используем обновленный заголовок
    documentation = f"""{README_HEADER}
{structure}
## 💻 Коды основных модулей
{code_sections}
"""

    # Запись README.md
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(documentation)
    print("[+] README.md успешно обновлён")

    # --- Создание .docx ---
    # Создаем каталог documents, если он не существует
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    project_name = PROJECT_ROOT.name
    docx_filename = f"{project_name}_{timestamp}.docx"
    docx_path = DOCS_DIR / docx_filename

    doc = Document()
    style = doc.styles['Normal']
    font = style.font # type: ignore
    font.name = 'Consolas'
    font.size = Pt(10)

    # Разбиваем всю документацию на строки
    lines = documentation.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Очищаем каждую строку перед добавлением
        clean_line = clean_text_for_xml(line)
        
        if clean_line.startswith("```"):
            # Начало блока кода
            lang = clean_line[3:].strip() # Получаем язык (например, python)
            code_block = ""
            i += 1
            # Собираем строки кода до закрывающей ```
            while i < len(lines) and not lines[i].startswith("```"):
                # Очищаем и добавляем каждую строку кода
                code_block += clean_text_for_xml(lines[i]) + "\n"
                i += 1
            # Добавляем блок кода в документ
            if code_block.strip():
                p_code = doc.add_paragraph(code_block.strip())
                # Простая попытка применить стиль кода (docx не поддерживает подсветку синтаксиса из коробки)
                # Можно рассмотреть использование python-docx-template или других библиотек
                # p_code.style = 'Code' if 'Code' in [s.name for s in doc.styles] else 'Normal'
            i += 1 # Пропускаем закрывающую ```
            continue # Переходим к следующей итерации внешнего цикла
        else:
            # Обычный текст
            if clean_line: # Добавляем только непустые строки
                 p = doc.add_paragraph(clean_line)
                 p.style = doc.styles['Normal'] # type: ignore
        i += 1 # Переход к следующей строке

    try:
        doc.save(docx_path) # type: ignore
        print(f"[+] Документация сохранена как {docx_path}")
    except Exception as e:
        print(f"[!] Ошибка при сохранении .docx файла: {e}")

if __name__ == "__main__":
    build_documentation()
    print("[+] Генерация документации завершена")
```
### 📄 `init_schema.sql`

```
-- init_schema.sql
-- PostgreSQL 12+ (для gen_random_uuid и JSONB функций)

-- UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- === 1. Каноническая таблица метрик (с партиционированием) ===
CREATE TABLE IF NOT EXISTS canonical_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dimensions JSONB NOT NULL DEFAULT '{}',
    tags JSONB NOT NULL DEFAULT '{}',
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Индексы на родительской таблице
CREATE INDEX IF NOT EXISTS idx_canonical_metric ON canonical_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_canonical_dimensions_gin ON canonical_metrics USING GIN (dimensions);
CREATE INDEX IF NOT EXISTS idx_canonical_tags_gin ON canonical_metrics USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_canonical_metric_ts ON canonical_metrics (metric_name, timestamp DESC);

-- Пример партиции (автоматизируется в Celery)
CREATE TABLE IF NOT EXISTS canonical_metrics_2025_11
PARTITION OF canonical_metrics
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE INDEX IF NOT EXISTS idx_canonical_2025_11_ts ON canonical_metrics_2025_11 (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_2025_11_metric_ts_region
ON canonical_metrics_2025_11 (metric_name, timestamp DESC, (dimensions->>'region'));
-- 🔍 Критические индексы
CREATE INDEX IF NOT EXISTS idx_canonical_ts ON canonical_metrics (timestamp DESC);
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
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    alert_event_id UUID REFERENCES alert_events(id) ON DELETE SET NULL,
    external_id TEXT,  -- id в i-doit / Jira и т.д.
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    priority TEXT NOT NULL,
    assigned_to TEXT,
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

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_canonical_metric_ts_region
ON canonical_metrics (
  metric_name,
  timestamp DESC,
  (dimensions->>'region')
);

-- ✅ Готово. Схема инициализирована.
```
### 📄 `instructions.md`

```markdown
# Инициациация базы данных

psql -h localhost -U postgres -d monitoring_db -f init_schema.sql


```
### 📄 `kafka_consumer_main.py`

```python
# kafka_consumer_main.py
"""Entry point for the Kafka consumer service."""
from config import settings, logger

if __name__ == "__main__":
    bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    logger.info("Starting Kafka consumer with bootstrap: %s", bootstrap)

    from core.kafka_consumer import MetricKafkaConsumer
    consumer = MetricKafkaConsumer(bootstrap_servers=bootstrap)
    consumer.run()

```
### 📄 `requirements.txt`

```
aiohttp>=3.9,<4
alembic>=1.13,<2
pandas>=2.1,<3
requests>=2.31,<3
pydantic>=2.5,<3
pydantic_settings>=2.1,<3
python-docx>=1.1,<2
pathspec>=0.12,<1
diskcache>=5.6,<6
python-dotenv>=1.0,<2
pytest>=8.0,<10
pytest-mock>=3.12,<4
xlsxwriter>=3.1,<4
tenacity>=8.2,<10
psycopg2-binary>=2.9,<3
sqlalchemy>=2.0,<3
redis>=5.0,<8
fakeredis>=2.20,<3
celery>=5.3,<6
prophet>=1.1
scikit-learn>=1.3
joblib>=1.3,<2
tensorflow>=2.14
h5py>=3.10,<4
kafka-python>=2.0,<3
fastapi>=0.109,<1
uvicorn[standard]>=0.27,<1
python-jose[cryptography]>=3.3,<4
prometheus_client>=0.19,<1
slowapi>=0.1.9,<1
psutil>=5.9,<7
fastapi-jwt-auth>=0.5,<1
pytest-cov>=4.1,<6
pytest-asyncio>=0.23,<1
httpx>=0.27,<1
torch>=2.1
passlib>=1.7,<2
bcrypt>=4.1,<6
python-multipart>=0.0.6,<1
clickhouse-connect>=0.7,<1
ldap3>=2.9,<3
authlib>=1.3,<2
itsdangerous>=2.1,<3
locust>=2.20,<3
opentelemetry-api>=1.22,<2
opentelemetry-sdk>=1.22,<2
opentelemetry-exporter-otlp-proto-grpc>=1.22,<2
opentelemetry-instrumentation-fastapi>=0.43b0
opentelemetry-instrumentation-sqlalchemy>=0.43b0
opentelemetry-instrumentation-redis>=0.43b0
opentelemetry-instrumentation-requests>=0.43b0

```
### 📄 `tasks.py`

```python
# tasks.py
import pandas as pd
from sqlalchemy import text
from celery_app import celery_app
from core.database import get_engine
from core.smart_alerts import check_growth_alert
from core.alert_settings import load_alert_settings_cached
from config import logger, get_redis
from core.notifications import notify
from telegram_bot import send_alert_sync
from celery.signals import task_failure
from datetime import datetime, timezone
from hashlib import md5


def get_data_from_db(time_filter: str = "1h") -> pd.DataFrame:
    delta_map = {"1h": 1, "6h": 6, "24h": 24}
    hours = delta_map.get(time_filter, 1)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)

    engine = get_engine()
    
    # 🔒 ИСПРАВЛЕНО: безопасный параметризованный запрос
    query = text("""
        SELECT
            date_trunc('hour', cm.timestamp AT TIME ZONE 'UTC') AS hour,
            cm.dimensions->>'region' AS region,
            MAX(CASE WHEN cm.metric_name = 'complaints' THEN cm.value END) AS complaints,
            MAX(CASE WHEN cm.metric_name = 'closed' THEN cm.value END) AS closed
        FROM canonical_metrics cm
        WHERE cm.metric_name = ANY(:metric_names)
          AND cm.timestamp >= :cutoff
          AND cm.dimensions ? 'region'
        GROUP BY hour, cm.dimensions->>'region'
        ORDER BY hour DESC
    """)
    return pd.read_sql(query, engine, params={
        "metric_names": ["complaints", "closed"],
        "cutoff": cutoff
    }) # type: ignore


@celery_app.task(bind=True, max_retries=3)
def run_alerts_check_task(self, time_filter: str = "1h"):
    try:
        df = get_data_from_db(time_filter)
        if df.empty:
            return {"status": "no_data"}

        alert_settings = load_alert_settings_cached()
        alerts = []

        for col, name in [("complaints", "Жалобы"), ("closed", "Сеть")]:
            msg = check_growth_alert(df, col, name, alert_settings)
            if msg:
                notify(msg, "critical")
                alerts.append({"metric": name, "alert": msg})

        return {"status": "success", "alerts": alerts}
    except Exception as exc:
        logger.exception("❌ Celery task failed")
        raise self.retry(exc=exc, countdown=30)



@celery_app.task(bind=True, max_retries=3)
def send_notification(self, message: str, priority: str, idempotency_key: str = None): # type: ignore
    if not idempotency_key:
        idempotency_key = md5(f"{message}:{priority}".encode()).hexdigest()[:16]

    cache = get_redis()
    cache_key = f"notification_sent:{idempotency_key}"
    if cache.get(cache_key):
        logger.info(f"🔇 Дубликат уведомления (idempotency_key={idempotency_key})")
        return True

    try:
        success = send_alert_sync(message, priority)
        if success:
            cache.setex(cache_key, 3600, "1")  # 1 час дедупликации
        return success
    except Exception as e:
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task
def update_mv_data():
    try:
        from core.data import create_mv
        if create_mv():
            logger.info("✅ MV обновлены")
        else:
            logger.warning("⚠️ Не удалось обновить MV")
    except Exception as e:
        logger.exception("⚠️ Ошибка при обновлении MV")


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    try:
        task_name = getattr(sender, "name", sender)
        if task_name == "tasks.send_notification":
            args = kwargs.get("args", [])
            message = str(args[0]) if len(args) > 0 else ""
            priority = str(args[1]) if len(args) > 1 else "info"
            
            payload = {
                "task_id": task_id or "",
                "message": message,
                "priority": priority,
                "error": str(exception),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            try:
                get_redis().xadd("dlq:notifications", payload) # type: ignore
                logger.error(f"🚨 DLQ запись: {message[:50]}...")
            except Exception as e:
                logger.exception("❌ Ошибка записи в DLQ")
    except Exception:
        logger.exception("💥 Ошибка в handle_task_failure")
        
@celery_app.task
def check_sla_breaches_task():
    try:
        from core.sla_service import check_sla_breaches
        result = check_sla_breaches()
        if result["response_breaches"] or result["resolution_breaches"]:
            logger.warning(f"SLA breaches: {result}")
        return result
    except Exception as e:
        logger.exception("SLA breach check failed")


@celery_app.task
def check_auto_escalation_task():
    try:
        from core.sla_service import check_auto_escalation
        check_auto_escalation()
    except Exception as e:
        logger.exception("Auto-escalation check failed")


@celery_app.task
def healthcheck():
    return {"status": "ok"}



```
### 📄 `telegram_bot.py`

```python
# telegram_bot.py

import requests
from config import logger, settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.locking import global_lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Эмодзи для приоритетов
PRIORITY_EMOJI = {
    "info": "ℹ️",
    "warning": "🟡",
    "critical": "🔴",
    "error": "❌"
}

# Глобальная сессия (thread-safe)
_telegram_session = None


def get_session():
    global _telegram_session
    with global_lock("telegram_session"):
        if _telegram_session is None:
            _telegram_session = requests.Session()
            
            # Настройка retry на уровне сессии
            retry_strategy = Retry(
                total=3,  # Максимум 3 попытки
                backoff_factor=1,  # Экспоненциальная задержка
                status_forcelist=[429, 500, 502, 503, 504],  # Повтор на этих кодах
                allowed_methods=["POST"]  # Только POST
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            _telegram_session.mount("https://", adapter)
            _telegram_session.mount("http://", adapter)
            
            _telegram_session.headers.update({"User-Agent": "SituationalCenter/1.0"})
            logger.debug("Создана новая requests.Session для Telegram с retry")
        
        return _telegram_session

def close_telegram_session_sync():
    global _telegram_session
    with global_lock("telegram_session_close"):
        try:
            if _telegram_session is not None:
                # у requests.Session есть метод close()
                close_fn = getattr(_telegram_session, "close", None)
                if callable(close_fn):
                    close_fn()
                _telegram_session = None
                logger.info("✅ Telegram session закрыта")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии Telegram session: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((
        requests.Timeout,
        requests.ConnectionError,
        requests.HTTPError
    )),
    reraise=False,  # Не поднимаем исключение после всех попыток
    before_sleep=lambda retry_state: logger.warning(
        f"Повторная попытка отправки уведомления ({retry_state.attempt_number}/3)..."
    ),
    after=lambda retry_state: logger.error(
        f"Не удалось отправить уведомление после {retry_state.attempt_number} попыток"
    ) if retry_state.outcome.failed else None # type: ignore
)
def send_alert_sync(message: str, priority: str = "info") -> bool:
    """
    Синхронная отправка уведомления в Telegram с retry и таймаутами.
    
    Returns:
        bool: True если отправлено успешно, False иначе
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    # Выбор чата по приоритету
    chat_id = settings.TELEGRAM_CHAT_ID
    if priority == "critical":
        chat_id = settings.TELEGRAM_CHAT_ID_CRITICAL or chat_id
    elif priority == "warning":
        chat_id = settings.TELEGRAM_CHAT_ID_WARNING or chat_id
    
    if not chat_id:
        logger.error(f"ID чата не определён для приоритета {priority}")
        return False

    emoji = PRIORITY_EMOJI.get(priority, "ℹ️")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"{emoji} {message}",
        "parse_mode": "HTML",
        "disable_notification": priority == "info",
    }

    session = get_session()
    try:
        # Таймауты: (connect, read)
        resp = session.post(url, json=payload, timeout=(5, 10))
        resp.raise_for_status()
        
        result = resp.json()
        if result.get("ok"):
            logger.info(f"✅ Telegram: {message[:50]}...")
            return True
        else:
            err = result.get("description", "неизвестная ошибка API")
            logger.error(f"❌ Telegram API: {err}")
            return False
    
    except requests.Timeout:
        logger.error(f"⏰ Таймаут при отправке в Telegram ({url})")
        raise  # Retry сработает
    
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        if status_code == 429:
            logger.warning("🚦 Telegram Rate Limit — ждем...")
            raise  # Retry с backoff
        elif status_code and 500 <= status_code < 600:
            logger.error(f"🔥 Telegram server error: {status_code}")
            raise  # Retry
        else:
            logger.error(f"❌ Telegram HTTP error: {e}")
            return False  # Не ретраим
    
    except requests.ConnectionError as e:
        logger.error(f"📡 Ошибка подключения к Telegram: {e}")
        raise  # Retry
    
    except Exception as e:
        logger.exception(f"💥 Неожиданная ошибка при отправке в Telegram: {e}")
        return False
```
### 📄 `wait-for-db-and-start.sh`

```bash
#!/bin/sh

set -e # Завершить скрипт, если любая команда завершится ошибкой

echo "Ожидание готовности PostgreSQL..."

# Простой цикл ожидания
# Убедитесь, что утилита pg_isready доступна в образе вашего приложения
# (она обычно есть в образах с PostgreSQL client или если установлен пакет postgresql-client)
until pg_isready -h "$POSTGRES_SERVER" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  >&2 echo "PostgreSQL недоступен - ожидание..."
  sleep 2
done

>&2 echo "PostgreSQL готов."

# Применяем миграции Alembic
>&2 echo "📦 Применяем миграции Alembic..."
alembic upgrade head

# Проверяем, нужно ли инициализировать данные
# Здесь можно добавить логику проверки существования данных
# Пока просто запускаем generate_data.py (он должен быть идемпотентным или проверять существование)
>&2 echo "Создаём/проверяем таблицы и генерируем данные..."
python generate_data.py
```
### 📄 `api/Dockerfile.api`

```
# api/Dockerfile.api — исправленная версия

# Stage 1: сборка зависимостей
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Устанавливаем в /root/.local для builder
RUN pip install --user --no-cache-dir -r requirements.txt


# Stage 2: production-образ
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos '' appuser

RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# ИСПРАВЛЕНО: копируем из /root/.local в /home/appuser/.local
COPY --from=builder /root/.local /home/appuser/.local

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

COPY --chown=appuser:appuser . .

ENV MPLCONFIGDIR=/home/appuser/.matplotlib

EXPOSE 8000

COPY .env .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```
### 📄 `api/__init__.py`

```python

```
### 📄 `api/auth.py`

```python
# api/auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from config import settings

if not settings.secret_key:
    raise RuntimeError("SECRET_KEY is not set. Set SECRET_KEY in env or .env and restart the app.")

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    tenant_id: str = "default"
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # type: ignore
        scopes = payload.get("scopes", [])
        tenant_id = payload.get("tenant_id", "default")
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])
        if username is None:
            raise JWTError()
        return TokenData(
            username=username,
            scopes=scopes,
            tenant_id=tenant_id,
            roles=roles,
            permissions=permissions,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)

```
### 📄 `api/dependencies.py`

```python
# api/dependencies.py
from core.metadata_service import metadata_service
from core.database import get_engine
from core.tenant import set_current_tenant
from api.auth import get_current_user, TokenData
from fastapi import Depends, HTTPException


def get_metadata_service():
    return metadata_service


def get_db_engine():
    return get_engine()


def require_scope(required_scope: str):
    def _check(current_user: TokenData = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return _check


def get_tenant_context(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Set tenant context from JWT and return the user."""
    set_current_tenant(current_user.tenant_id)
    return current_user

```
### 📄 `api/limiter.py`

```python
# api/limiter.py
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings

_storage_uri = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Use in-memory storage for testing (when TESTING env var is set)
if os.getenv("TESTING", "").lower() in ("1", "true"):
    _storage_uri = "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri=_storage_uri,
    strategy="fixed-window"
)

```
### 📄 `api/main.py`

```python
# api/main.py
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import logger, setup_logging, settings

# Настройка логирования (важно: до импорта других модулей)
setup_logging()

from api.routes import metrics, dimensions, rules, ml_configs, alerts, data, webhooks, admin, incidents, forecasts
from api.routes import auth as auth_routes
from api.routes import audit as audit_routes
from api.auth import Token, OAuth2PasswordRequestForm
from core.exceptions import (
    situational_center_error_handler,
    sqlalchemy_error_handler,
    SituationalCenterError
)

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from api.middleware import PrometheusMiddleware, DeprecationMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import DatabaseError as SQLADatabaseError
from api.limiter import limiter
ALERTS_SENT = Counter("alerts_sent_total", "Total alerts sent", ["priority"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from api.routes.websocket import alert_stream_task
    logger.info("🚀 Запуск API-сервера...")

    # Configure OIDC if enabled
    try:
        from core.oidc_auth import configure_oidc
        configure_oidc()
    except Exception as e:
        logger.warning(f"OIDC configuration failed: {e}")

    # Configure OpenTelemetry tracing if enabled
    try:
        from core.tracing import setup_tracing
        setup_tracing(app)
    except Exception as e:
        logger.warning(f"OpenTelemetry setup failed: {e}")

    # Start incident buffer processor (moved from module-level import)
    from core.alerts import start_incident_buffer_processor
    start_incident_buffer_processor()

    asyncio.create_task(alert_stream_task())
    yield
    logger.info("🛑 Остановка API-сервера...")

app = FastAPI(
    title="Situational Center API",
    description="REST API для управления ситуационным центром",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(DeprecationMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore
app.add_exception_handler(SituationalCenterError, situational_center_error_handler) # type: ignore
app.add_exception_handler(SQLADatabaseError, sqlalchemy_error_handler) # type: ignore


# CORS — origins from CORS_ORIGINS env var (comma-separated)
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-KEY", "Accept"],
)



# API v1 — all business routes under /api/v1/ prefix
API_V1_PREFIX = "/api/v1"
app.include_router(metrics.router, prefix=API_V1_PREFIX)
app.include_router(dimensions.router, prefix=API_V1_PREFIX)
app.include_router(rules.router, prefix=API_V1_PREFIX)
app.include_router(ml_configs.router, prefix=API_V1_PREFIX)
app.include_router(alerts.router, prefix=API_V1_PREFIX)
app.include_router(data.router, prefix=API_V1_PREFIX)
app.include_router(webhooks.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(incidents.router, prefix=API_V1_PREFIX)
app.include_router(forecasts.router, prefix=API_V1_PREFIX)
app.include_router(auth_routes.router, prefix=API_V1_PREFIX)
app.include_router(audit_routes.router, prefix=API_V1_PREFIX)

# Backward-compat: also mount without prefix for existing clients
app.include_router(metrics.router)
app.include_router(dimensions.router)
app.include_router(rules.router)
app.include_router(ml_configs.router)
app.include_router(alerts.router)
app.include_router(data.router)
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(incidents.router)
app.include_router(forecasts.router)
app.include_router(auth_routes.router)
app.include_router(audit_routes.router)

# WebSocket
from api.routes.websocket import router as ws_router
app.include_router(ws_router)

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    from core.auth_strategies import try_ldap_auth, try_db_auth, try_env_admin_auth
    from core.audit import log_audit
    ip = request.client.host if request.client else None

    # 1) LDAP
    token = try_ldap_auth(form_data.username, form_data.password)
    if token:
        log_audit(form_data.username, "default", "login", "session", ip_address=ip)
        return {"access_token": token, "token_type": "bearer"}

    # 2) DB user
    db_result = try_db_auth(form_data.username, form_data.password)
    if db_result:
        log_audit(db_result["username"], db_result["tenant_id"], "login", "session", ip_address=ip)
        return {"access_token": db_result["token"], "token_type": "bearer"}

    # 3) Env-based admin fallback
    token = try_env_admin_auth(form_data.username, form_data.password)
    log_audit(form_data.username, "default", "login", "session", ip_address=ip)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "situational-center-api"}

@app.get("/metric")
async def metric():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
    

```
### 📄 `api/middleware.py`

```python
# api/middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Histogram, Counter, Gauge

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method"],
)

# --- SQLAlchemy connection pool metrics ---

sqlalchemy_pool_size = Gauge(
    "sqlalchemy_pool_size",
    "Number of connections currently in the pool (checked in + checked out)",
)

sqlalchemy_pool_checked_in = Gauge(
    "sqlalchemy_pool_checked_in",
    "Number of idle connections in the pool",
)

sqlalchemy_pool_checked_out = Gauge(
    "sqlalchemy_pool_checked_out",
    "Number of connections currently checked out (in use)",
)

sqlalchemy_pool_overflow = Gauge(
    "sqlalchemy_pool_overflow",
    "Current overflow connections beyond pool_size",
)


def collect_pool_metrics():
    """Update SQLAlchemy pool gauges from the current engine's QueuePool."""
    try:
        from core.database import _engine
        if _engine is None:
            return
        pool = _engine.pool
        sqlalchemy_pool_size.set(pool.size())
        sqlalchemy_pool_checked_in.set(pool.checkedin())
        sqlalchemy_pool_checked_out.set(pool.checkedout())
        sqlalchemy_pool_overflow.set(pool.overflow())
    except Exception:
        pass


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        # Normalize path to avoid high-cardinality labels
        path = request.url.path
        for segment in path.split("/"):
            if segment and (len(segment) > 30 or _looks_like_id(segment)):
                path = path.replace(segment, "{id}")

        http_requests_in_progress.labels(method=method).inc()
        collect_pool_metrics()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            http_request_duration_seconds.labels(method=method, path=path, status_code=status_code).observe(duration)
            http_requests_total.labels(method=method, path=path, status_code=status_code).inc()
            http_requests_in_progress.labels(method=method).dec()

        return response


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add Deprecation header to legacy routes (without /api/v1/ prefix)."""

    LEGACY_PREFIXES = (
        "/metrics", "/dimensions", "/rules", "/ml/", "/alerts",
        "/data", "/webhooks", "/admin", "/incidents", "/forecasts",
        "/auth", "/audit",
    )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api/v1") and any(path.startswith(p) for p in self.LEGACY_PREFIXES):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-09-01"
            response.headers["Link"] = f'</api/v1{path}>; rel="successor-version"'
        return response


def _looks_like_id(segment: str) -> bool:
    """Heuristic: UUIDs, numeric IDs, hex strings."""
    if segment.isdigit():
        return True
    if len(segment) == 36 and segment.count("-") == 4:
        return True
    try:
        if len(segment) >= 8:
            int(segment, 16)
            return True
    except ValueError:
        pass
    return False

```
### 📄 `api/schemas.py`

```python
# api/schemas.py
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


# --- Metrics ---
class MetricCreate(BaseModel):
    metric_name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    unit: str = ""
    default_threshold: Optional[float] = None
    default_critical_threshold: Optional[float] = None
    is_active: bool = True

class MetricUpdate(MetricCreate):
    pass  # PUT — полная замена

class MetricRead(MetricCreate):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Dimensions ---
class DimensionCreate(BaseModel):
    dimension_key: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
    description: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    is_required: bool = False

class DimensionRead(DimensionCreate):
    created_at: datetime

    class Config:
        from_attributes = True


# --- Actions (для правил) ---
class Action(BaseModel):
    type: str = Field(..., description="telegram, webhook, idoit, incident, etc.")
    config: Dict[str, Any]


# --- Rules ---
class RuleCondition(BaseModel):
    expr: str = Field(..., description="PromQL-style: metric{dim='val'} > 100")
    for_duration: str = Field("1m", alias="for", description="duration: '5m', '1h'")
    eval_interval: str = Field("1m", alias="eval", description="evaluation interval")
    
    class Config:
        populate_by_name = True
        
    # Добавить validator для формата времени
    @validator('for_duration', 'eval_interval')
    def validate_duration(cls, v):
        import re
        if not re.match(r'^\d+[smhd]$', v):
            raise ValueError('Duration must be in format: 1s, 5m, 1h, 1d')
        return v

class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    condition: RuleCondition
    labels: Dict[str, str] = Field(default_factory=dict)
    actions: List[Action] = Field(default_factory=list)
    is_active: bool = True

class RuleUpdate(RuleCreate):
    pass

class RuleRead(RuleCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- ML Configs ---
class MLConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    metric_name: str
    group_by: List[str] = Field(default_factory=list)
    methods: List[str] = Field(["prophet"])
    method_params: Dict[str, Any] = Field(default_factory=dict)
    retrain_schedule: str = "0 3 * * *"
    auto_alert: bool = True
    alert_severity: Literal["info", "warning", "critical"] = "warning"
    is_active: bool = True

class MLConfigUpdate(MLConfigCreate):
    pass

class MLConfigRead(MLConfigCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Data Query ---
class DataQueryRequest(BaseModel):
    metric_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dimensions: Optional[Dict[str, str]] = None  # exact match: {"region": "RU-MOW"}
    dimension_in: Optional[Dict[str, List[str]]] = None  # IN: {"service": ["auth", "billing"]}
    limit: int = Field(1000, ge=1, le=10000)

class DataPoint(BaseModel):
    timestamp: datetime
    value: float
    dimensions: Dict[str, str]
    tags: Dict[str, str]

class DataQueryResponse(BaseModel):
    metric_name: str
    points: List[DataPoint]
    total: int


# --- Alerts ---
class AlertRead(BaseModel):
    id: UUID
    rule_id: Optional[UUID] = None
    ml_config_id: Optional[UUID] = None
    metric_name: str
    dimensions: Dict[str, str]
    value: float
    event_time: datetime
    detected_at: datetime
    status: Literal["firing", "acknowledged", "resolved"]
    sent: bool
    fingerprint: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    class Config:
        from_attributes = True


# --- Incidents ---
class IncidentCreate(BaseModel):
    alert_message: str = Field(..., min_length=1, max_length=1000)
    metric: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    value: Optional[str] = None
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    alert_event_id: Optional[UUID] = None


class IncidentStatusUpdate(BaseModel):
    status: Literal["new", "in_progress", "escalated", "resolved", "closed"]
    comment: Optional[str] = None


class IncidentAssign(BaseModel):
    assigned_to: str = Field(..., min_length=1, max_length=100)
    comment: Optional[str] = None


class IncidentCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class IncidentCommentRead(BaseModel):
    id: int
    incident_id: int
    author: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentRead(BaseModel):
    id: int
    alert_message: str
    metric: str
    region: str
    value: Optional[str] = None
    priority: str
    status: str
    detected_at: datetime
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    description: Optional[str] = None
    alert_event_id: Optional[UUID] = None
    response_deadline: Optional[datetime] = None
    resolution_deadline: Optional[datetime] = None
    response_breached: bool = False
    resolution_breached: bool = False
    escalation_level: int = 0
    last_escalated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_system: Optional[str] = None
    external_url: Optional[str] = None

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    items: List[IncidentRead]
    total: int


# --- SLA ---
class SlaPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    priority: Literal["critical", "high", "medium", "low"]
    response_time_minutes: int = Field(..., gt=0)
    resolution_time_minutes: int = Field(..., gt=0)
    escalation_after_minutes: int = Field(..., gt=0)


class SlaPolicyRead(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    priority: str
    response_time_minutes: int
    resolution_time_minutes: int
    escalation_after_minutes: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Forecasts ---
class ForecastPoint(BaseModel):
    timestamp: datetime
    value: float
    lower: Optional[float] = None
    upper: Optional[float] = None


class ForecastResponse(BaseModel):
    metric_name: str
    dimensions: Dict[str, str]
    horizon_hours: int
    points: List[ForecastPoint]
```
### 📄 `api/routes/__init__.py`

```python

```
### 📄 `api/routes/admin.py`

```python
# api/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import text
from core.database import get_engine
from core.rbac import require_role
from core.audit import log_audit
from api.auth import TokenData
from config import mask_secrets

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Schemas ---

class TenantCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=1, max_length=200)


class TenantRead(BaseModel):
    id: str
    name: str
    is_active: bool


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    password: Optional[str] = None
    tenant_id: str = "default"


class UserRead(BaseModel):
    id: UUID
    username: str
    email: Optional[str]
    tenant_id: str
    is_active: bool
    auth_provider: str


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    tenant_id: str = "default"
    permissions: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class RoleRead(BaseModel):
    id: UUID
    name: str
    tenant_id: str
    permissions: list
    description: Optional[str]


class UserRoleAssign(BaseModel):
    user_id: UUID
    role_id: UUID


# --- Tenants ---

@router.get("/tenants", response_model=List[TenantRead])
def list_tenants(current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, is_active FROM tenants ORDER BY id")).mappings().all()
        return [TenantRead(**row) for row in rows]


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant(data: TenantCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
                {"id": data.id, "name": data.name},
            )
        log_audit(current_user.username, current_user.tenant_id, "create", "tenant", resource_id=data.id)
        return TenantRead(id=data.id, name=data.name, is_active=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- Users ---

@router.get("/users", response_model=List[UserRead])
def list_users(tenant_id: str = "default", current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, username, email, tenant_id, is_active, auth_provider FROM users WHERE tenant_id = :tid ORDER BY username"),
            {"tid": tenant_id},
        ).mappings().all()
        return [UserRead(**row) for row in rows]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    password_hash = None
    if data.password:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(data.password)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, tenant_id)
                    VALUES (:username, :email, :password_hash, :tenant_id)
                    RETURNING id, username, email, tenant_id, is_active, auth_provider
                """),
                {
                    "username": data.username,
                    "email": data.email,
                    "password_hash": password_hash,
                    "tenant_id": data.tenant_id,
                },
            ).mappings().first()
            log_audit(current_user.username, current_user.tenant_id, "create", "user", resource_id=data.username)
            return UserRead(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- Roles ---

@router.get("/roles", response_model=List[RoleRead])
def list_roles(tenant_id: str = "default", current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, tenant_id, permissions, description FROM roles WHERE tenant_id = :tid ORDER BY name"),
            {"tid": tenant_id},
        ).mappings().all()
        return [RoleRead(**row) for row in rows]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreate, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    import json
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO roles (name, tenant_id, permissions, description)
                    VALUES (:name, :tenant_id, :permissions, :description)
                    RETURNING id, name, tenant_id, permissions, description
                """),
                {
                    "name": data.name,
                    "tenant_id": data.tenant_id,
                    "permissions": json.dumps(data.permissions),
                    "description": data.description,
                },
            ).mappings().first()
            log_audit(current_user.username, current_user.tenant_id, "create", "role", resource_id=data.name)
            return RoleRead(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


# --- User-Role assignment ---

@router.post("/user-roles", status_code=status.HTTP_201_CREATED)
def assign_role(data: UserRoleAssign, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid) ON CONFLICT DO NOTHING"),
                {"uid": data.user_id, "rid": data.role_id},
            )
        log_audit(current_user.username, current_user.tenant_id, "assign_role", "user_role",
                  resource_id=str(data.user_id), changes={"role_id": str(data.role_id)})
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, mask_secrets(str(e)))


@router.delete("/user-roles", status_code=status.HTTP_204_NO_CONTENT)
def unassign_role(data: UserRoleAssign, current_user: TokenData = Depends(require_role("admin"))):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid AND role_id = :rid"),
            {"uid": data.user_id, "rid": data.role_id},
        )
    log_audit(current_user.username, current_user.tenant_id, "unassign_role", "user_role",
              resource_id=str(data.user_id), changes={"role_id": str(data.role_id)})

```
### 📄 `api/routes/alerts.py`

```python
# api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from api.schemas import AlertRead
from sqlalchemy import text
from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from config import mask_secrets

router = APIRouter(prefix="/alerts", tags=["Alerts"])


ALERT_FIELDS = """id, rule_id, ml_config_id, metric_name, dimensions, value,
    event_time, detected_at, status, sent, fingerprint,
    acknowledged_by, acknowledged_at, resolved_by, tenant_id"""


def _row_to_alert(row) -> AlertRead:
    return AlertRead(
        id=row["id"],
        rule_id=row["rule_id"],
        ml_config_id=row["ml_config_id"],
        metric_name=row["metric_name"],
        dimensions=row["dimensions"] or {},
        value=row["value"],
        event_time=row["event_time"],
        detected_at=row["detected_at"],
        status=row["status"],
        sent=row["sent"],
        fingerprint=row["fingerprint"],
        acknowledged_by=row.get("acknowledged_by"),
        acknowledged_at=row.get("acknowledged_at"),
        resolved_by=row.get("resolved_by"),
    )


@router.get("/", response_model=List[AlertRead])
def list_alerts(
    status: str = Query(None, enum=["firing", "acknowledged", "resolved"]),
    metric_name: str = None,  # type: ignore
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    where_clauses = ["tenant_id = :tenant_id"]
    params = {"limit": limit, "offset": offset, "tenant_id": current_user.tenant_id}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status  # type: ignore
    if metric_name:
        where_clauses.append("metric_name = :metric_name")
        params["metric_name"] = metric_name  # type: ignore

    where = "WHERE " + " AND ".join(where_clauses)

    query = text(f"""
        SELECT {ALERT_FIELDS}
        FROM alert_events
        {where}
        ORDER BY event_time DESC
        LIMIT :limit OFFSET :offset
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [_row_to_alert(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    query = text(f"""
        SELECT {ALERT_FIELDS}
        FROM alert_events
        WHERE id = :alert_id AND tenant_id = :tenant_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"alert_id": alert_id, "tenant_id": current_user.tenant_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")
            return _row_to_alert(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.post("/{alert_id}/suppress", status_code=204)
def suppress_alert(
    alert_id: UUID,
    minutes: int = 60,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT fingerprint FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")

            from core.alerts import suppress_alert as _suppress
            _suppress(row["fingerprint"], minutes)

        log_audit(current_user.username, current_user.tenant_id, "suppress", "alert", resource_id=str(alert_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()

            if not row:
                raise HTTPException(404, "Alert not found")
            if row["status"] not in ("firing",):
                raise HTTPException(400, f"Cannot acknowledge alert in status '{row['status']}'")

            conn.execute(
                text("""
                    UPDATE alert_events SET
                        status = 'acknowledged',
                        acknowledged_by = :user,
                        acknowledged_at = :now
                    WHERE id = :id
                """),
                {"id": alert_id, "user": current_user.username, "now": now},
            )

            result = conn.execute(
                text(f"SELECT {ALERT_FIELDS} FROM alert_events WHERE id = :id"),
                {"id": alert_id},
            ).mappings().first()

        log_audit(current_user.username, current_user.tenant_id, "acknowledge", "alert", resource_id=str(alert_id))
        return _row_to_alert(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(
    alert_id: UUID,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM alert_events WHERE id = :id AND tenant_id = :tid"),
                {"id": alert_id, "tid": current_user.tenant_id},
            ).mappings().first()

            if not row:
                raise HTTPException(404, "Alert not found")
            if row["status"] == "resolved":
                raise HTTPException(400, "Alert already resolved")

            conn.execute(
                text("""
                    UPDATE alert_events SET
                        status = 'resolved',
                        resolved_at = :now,
                        resolved_by = :user
                    WHERE id = :id
                """),
                {"id": alert_id, "user": current_user.username, "now": now},
            )

            result = conn.execute(
                text(f"SELECT {ALERT_FIELDS} FROM alert_events WHERE id = :id"),
                {"id": alert_id},
            ).mappings().first()

        log_audit(current_user.username, current_user.tenant_id, "resolve", "alert", resource_id=str(alert_id))
        return _row_to_alert(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))

```
### 📄 `api/routes/audit.py`

```python
# api/routes/audit.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import text
from core.database import get_engine
from core.rbac import require_permission
from api.auth import TokenData
from config import mask_secrets

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogEntry(BaseModel):
    id: int
    username: str
    tenant_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    changes: Dict[str, Any]
    ip_address: Optional[str]
    timestamp: datetime


@router.get("/logs", response_model=List[AuditLogEntry])
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:audit")),
):
    engine = get_engine()
    where_parts = ["tenant_id = :tenant_id"]
    params: Dict[str, Any] = {
        "tenant_id": current_user.tenant_id,
        "limit": limit,
        "offset": offset,
    }

    if action:
        where_parts.append("action = :action")
        params["action"] = action
    if resource_type:
        where_parts.append("resource_type = :resource_type")
        params["resource_type"] = resource_type
    if username:
        where_parts.append("username = :username")
        params["username"] = username

    where_clause = " AND ".join(where_parts)
    query = text(f"""
        SELECT id, username, tenant_id, action, resource_type, resource_id, changes, ip_address, timestamp
        FROM audit_log
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [AuditLogEntry(**row) for row in rows]
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))

```
### 📄 `api/routes/auth.py`

```python
# api/routes/auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from datetime import timedelta
from config import settings, logger
from api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login/oidc")
async def login_oidc(request: Request):
    """Redirect user to Keycloak for OIDC login."""
    if not getattr(settings, "OIDC_ENABLED", False):
        raise HTTPException(501, "OIDC not enabled")

    from core.oidc_auth import oauth
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    redirect_uri = f"{base_url}/auth/callback/oidc"
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@router.get("/callback/oidc")
async def callback_oidc(request: Request):
    """Handle OIDC callback from Keycloak, create JWT."""
    if not getattr(settings, "OIDC_ENABLED", False):
        raise HTTPException(501, "OIDC not enabled")

    from core.oidc_auth import oauth
    try:
        token = await oauth.keycloak.authorize_access_token(request)
    except Exception as e:
        logger.error("OIDC callback error: %s", e)
        raise HTTPException(401, "OIDC authentication failed")

    userinfo = token.get("userinfo", {})
    username = userinfo.get("preferred_username") or userinfo.get("sub")
    email = userinfo.get("email")

    if not username:
        raise HTTPException(401, "No username in OIDC token")

    # Sync user to DB
    try:
        from sqlalchemy import text
        from core.database import get_engine
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, email, tenant_id, auth_provider, external_id, is_active)
                    VALUES (:username, :email, 'default', 'oidc', :sub, true)
                    ON CONFLICT (username) DO UPDATE SET
                        email = EXCLUDED.email,
                        auth_provider = 'oidc',
                        external_id = EXCLUDED.external_id,
                        is_active = true,
                        updated_at = NOW()
                """),
                {"username": username, "email": email, "sub": userinfo.get("sub", "")},
            )
    except Exception as e:
        logger.warning("Failed to sync OIDC user: %s", e)

    # Map Keycloak roles -> local permissions
    realm_access = token.get("access_token_claims", {}).get("realm_access", {})
    kc_roles = realm_access.get("roles", [])
    roles = kc_roles if kc_roles else ["viewer"]

    # Resolve permissions from DB roles
    permissions: list = []
    try:
        from sqlalchemy import text as _t
        with engine.connect() as conn:
            for role_name in roles:
                r = conn.execute(
                    _t("SELECT permissions FROM roles WHERE name = :name AND tenant_id = 'default'"),
                    {"name": role_name},
                ).mappings().first()
                if r:
                    import json as _json
                    perms = r["permissions"]
                    permissions.extend(_json.loads(perms) if isinstance(perms, str) else perms)
    except Exception as e:
        logger.warning("Failed to resolve OIDC permissions: %s", e)

    access_token = create_access_token(
        data={
            "sub": username,
            "scopes": ["admin"] if "admin" in roles else [],
            "tenant_id": "default",
            "roles": roles,
            "permissions": list(set(permissions)),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Audit log for OIDC login
    try:
        from core.audit import log_audit
        ip = request.client.host if request.client else None
        log_audit(username, "default", "login", "session", ip_address=ip)
    except Exception as e:
        logger.warning("Failed to log OIDC audit: %s", e)

    # Redirect to frontend with token
    base_url = getattr(settings, "OIDC_BASE_URL", str(request.base_url).rstrip("/"))
    return RedirectResponse(f"{base_url}/?token={access_token}")

```
### 📄 `api/routes/data.py`

```python
# api/routes/data.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Literal
from datetime import datetime, timezone
import json
import re
from api.schemas import DataPoint, DataQueryResponse, DataQueryRequest
from core.database import get_engine
from sqlalchemy import text
from api.auth import get_current_user, TokenData
from api.limiter import limiter
from config import mask_secrets, logger

router = APIRouter(prefix="/data", tags=["Data"])
ALLOWED_DIMENSIONS = {"service", "region", "dc", "env", "team"}
ALLOWED_AGGREGATIONS = {"avg", "sum", "min", "max", "count"}
MAX_QUERY_RESULTS = 10000


def safe_jsonb_eq(column_expr: str, param_prefix: str, key: str, value: str) -> tuple[str, dict]:
    """
    Возвращает безопасное выражение: dimensions->>:key = :value
    Защищает от SQL-инъекции.
    """
    # 🔐 Валидация ключа: только [a-zA-Z0-9_-], длина 1-50
    if not isinstance(key, str) or not re.match(r"^[a-zA-Z0-9_\-]{1,50}$", key):
        from core.exceptions import InvalidDimensionKeyError
        raise InvalidDimensionKeyError(key)

    # 🔐 Валидация значения
    if not isinstance(value, str) or len(value) > 200:
        raise HTTPException(400, "Dimension value too long or invalid type")
    if '"' in value or "'" in value or '\\' in value:
        raise HTTPException(400, "Dimension value contains forbidden characters")

    return (
        f"{column_expr}->>:key_{param_prefix} = :val_{param_prefix}",
        {f"key_{param_prefix}": key, f"val_{param_prefix}": value}
    )


def validate_label_name(label_name: str) -> str:
    """Валидирует имя лейбла для защиты от injection"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid label name: {label_name}. Use only alphanumeric and underscore."
        )
    if len(label_name) > 50:
        raise HTTPException(400, "Label name too long")
    return label_name


@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}


@router.get("/prometheus/api/v1/label/__name__/values", response_model=List[str])
def prometheus_label_values1(current_user: TokenData = Depends(get_current_user)):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT DISTINCT metric_name FROM canonical_metrics ORDER BY metric_name")
            )
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error fetching metric names: {mask_secrets(str(e))}")
        raise HTTPException(500, "Internal server error")


@router.get("/prometheus/api/v1/label/{label_name}/values", response_model=List[str])
def prometheus_label_values(label_name: str, current_user: TokenData = Depends(get_current_user)):
    if label_name == "__name__":
        return prometheus_label_values1()

    label_name = validate_label_name(label_name)

    if label_name not in ALLOWED_DIMENSIONS:
        raise HTTPException(
            status_code=403,
            detail=f"Dimension '{label_name}' not allowed. Allowed: {ALLOWED_DIMENSIONS}"
        )

    engine = get_engine()
    try:
        with engine.connect() as conn:
            has_key = conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM canonical_metrics WHERE dimensions ? :label_name LIMIT 1)"),
                {"label_name": label_name}
            ).scalar()
            if not has_key:
                return []

            values_query = text("""
                SELECT DISTINCT dimensions->>:label_name as value
                FROM canonical_metrics
                WHERE dimensions ? :label_name
                  AND dimensions->>:label_name IS NOT NULL
                ORDER BY value
                LIMIT 1000
            """)
            result = conn.execute(values_query, {"label_name": label_name})
            return [row[0] for row in result if row[0]]
    except Exception as e:
        logger.error(f"Error fetching label values for {label_name}: {mask_secrets(str(e))}")
        raise HTTPException(500, "Internal server error")


@router.get("/prometheus/api/v1/series", response_model=Dict[str, Any])
def prometheus_series(
    match: List[str] = Query(default=[], alias="match[]"),
    start: float = Query(None),
    end: float = Query(None),
    current_user: TokenData = Depends(get_current_user),
):
    if not match:
        raise HTTPException(status_code=400, detail="match[] is required")
    
    engine = get_engine()
    series_set = set()
    
    for pattern in match:
        match_obj = re.match(r'^([a-zA-Z0-9_\-\.]+)(?:\{(.*)\})?$', pattern)
        if not match_obj:
            continue
        metric_name, filters_str = match_obj.groups()
        
        # Строим запрос с параметрами
        where_parts = ["metric_name = :metric"]
        params: Dict[str, Any] = {"metric": metric_name}
        
        if filters_str:
            for i, kv in enumerate(filters_str.split(",")):
                kv = kv.strip()
                if "=" not in kv:
                    continue
                k, v = kv.split("=", 1)
                k = k.strip()
                v = v.strip('"\'').strip()
                
                # Валидация ключа
                k = validate_label_name(k)
                if k not in ALLOWED_DIMENSIONS:
                    raise HTTPException(400, f"Dimension '{k}' not allowed")
                
                # Параметризованный запрос
                param_key = f"key_{i}"
                param_val = f"val_{i}"
                where_parts.append(f"dimensions->>:{param_key} = :{param_val}")
                params[param_key] = k
                params[param_val] = v
        
        # Безопасный запрос
        where_clause = " AND ".join(where_parts)
        query = text(f"""
            SELECT DISTINCT metric_name, dimensions
            FROM canonical_metrics
            WHERE {where_clause}
            LIMIT 1000
        """)
        
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            for row in rows:
                label_set = {"__name__": row["metric_name"]}
                label_set.update(row["dimensions"] or {})
                series_set.add(json.dumps(label_set, sort_keys=True))
    
    return {"status": "success", "data": [json.loads(s) for s in series_set]}


MAX_STEP_SECONDS = 86400


def _parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise HTTPException(400, "step must be string")
    s = s.strip()
    if len(s) > 10:
        raise HTTPException(400, "step string too long")
    match = re.fullmatch(r"^(\d{1,6})([smhd])$", s)
    if not match:
        raise HTTPException(400, "Invalid step format. Use: '15s', '1m', '2h', '1d'")
    num_str, unit = match.groups()
    num = int(num_str)
    if num <= 0:
        raise HTTPException(400, "step must be positive")
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    seconds = num * multipliers[unit]
    if seconds > 86400:
        raise HTTPException(400, "step too large (max 1 day)")
    return seconds


@router.get("/prometheus/api/v1/query_range", response_model=Dict[str, Any])
def prometheus_query_range(
    query: str,
    start: float,
    end: float,
    step: str = "15s",
    aggregation: Literal["avg", "sum", "min", "max", "count"] = "avg",
    current_user: TokenData = Depends(get_current_user),
):
    match_obj = re.match(r'^([a-zA-Z0-9_\-\.]+)(?:\{(.*)\})?$', query)
    if not match_obj:
        raise HTTPException(400, "Invalid query format. Use: metric_name{label='value'}")

    metric_name, filters_str = match_obj.groups()

    from core.metadata_service import metadata_service
    valid_metrics = {m.metric_name for m in metadata_service.list_metrics(active_only=True)}
    if metric_name not in valid_metrics:
        raise HTTPException(404, f"Metric '{metric_name}' not found or inactive")

    if start >= end:
        raise HTTPException(400, "start must be before end")
    if end - start > 86400 * 30:
        raise HTTPException(400, "Time range too large (max 30 days)")

    try:
        step_sec = _parse_duration(step)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Invalid step: {mask_secrets(str(e))}")

    where = ["metric_name = :metric", "timestamp >= :start", "timestamp <= :end"]
    params = {
        "metric": metric_name,
        "start": datetime.fromtimestamp(start, tz=timezone.utc),
        "end": datetime.fromtimestamp(end, tz=timezone.utc),
        "step_sec": step_sec,
    }

    if filters_str:
        for i, kv in enumerate(filters_str.split(",")):
            kv = kv.strip()
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            v = v.strip('"\'').strip()
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed. Allowed: {ALLOWED_DIMENSIONS}")
            expr, p = safe_jsonb_eq("dimensions", f"filter_{i}", k, v)
            where.append(expr)
            params.update(p)

    if aggregation not in ALLOWED_AGGREGATIONS:
        aggregation = "avg"

    group_by_expr = f"floor(EXTRACT(EPOCH FROM timestamp) / :step_sec) * :step_sec"

    query_sql = text(f"""
        SELECT
            {group_by_expr} AS bin,
            dimensions,
            {aggregation}(value) AS value
        FROM canonical_metrics
        WHERE {" AND ".join(where)}
        GROUP BY bin, dimensions
        ORDER BY bin
        LIMIT :limit
    """)
    params["limit"] = MAX_QUERY_RESULTS

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(query_sql, params).mappings().all()

        series_map = {}
        for row in rows:
            dims = tuple(sorted((k, v) for k, v in (row["dimensions"] or {}).items()))
            key = (metric_name, dims)
            if key not in series_map:
                series_map[key] = {
                    "metric": {"__name__": metric_name, **dict(dims)},
                    "values": []
                }
            series_map[key]["values"].append([
                float(row["bin"]),
                str(round(row["value"], 6))
            ])

        result = list(series_map.values())
        return {
            "status": "success",
            "data": {"resultType": "matrix", "result": result}
        }

    except Exception as e:
        logger.exception("Error executing Prometheus query")
        raise HTTPException(500, "Query execution failed")


@router.get("/analytics/query_range", response_model=Dict[str, Any])
def analytics_query_range(
    metric_name: str = Query(...),
    start: float = Query(...),
    end: float = Query(...),
    aggregation: Literal["avg", "sum", "min", "max", "count"] = "avg",
    interval: str = Query("1h", pattern=r"^\d+[smhd]$"),
    current_user: TokenData = Depends(get_current_user),
):
    """Long-range analytics query routed to ClickHouse when enabled."""
    from config import settings as cfg
    start_dt = datetime.fromtimestamp(start, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end, tz=timezone.utc)

    if not getattr(cfg, "CLICKHOUSE_ENABLED", False):
        raise HTTPException(501, "ClickHouse analytics not enabled")

    interval_map = {"s": "SECOND", "m": "MINUTE", "h": "HOUR", "d": "DAY"}
    num = interval[:-1]
    unit = interval_map.get(interval[-1], "HOUR")
    ch_interval = f"{num} {unit}"

    from core.analytics_service import analytics_service
    data = analytics_service.query_metric_aggregation(
        metric_name=metric_name,
        start=start_dt,
        end=end_dt,
        aggregation=aggregation,
        interval=ch_interval,
    )
    return {"status": "success", "data": data}


@router.post("/query", response_model=DataQueryResponse)
@limiter.limit("30/minute")
async def query_data(
    request: DataQueryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    from core.metadata_service import metadata_service
    metric = metadata_service.get_metric(request.metric_name)
    if not metric or not metric.is_active:
        raise HTTPException(404, f"Metric '{request.metric_name}' not found")

    where = ["metric_name = :metric_name"]
    params = {"metric_name": request.metric_name}

    if request.start_time:
        where.append("timestamp >= :start")
        params["start"] = request.start_time # type: ignore
    if request.end_time:
        where.append("timestamp <= :end")
        params["end"] = request.end_time # type: ignore

    if request.dimensions:
        for i, (k, v) in enumerate(request.dimensions.items()):
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed")
            expr, p = safe_jsonb_eq("dimensions", f"dim_{i}", k, str(v))
            where.append(expr)
            params.update(p)

    if request.dimension_in:
        for i, (k, vals) in enumerate(request.dimension_in.items()):
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed")
            if not isinstance(vals, list) or len(vals) > 50:
                raise HTTPException(400, f"Too many values for {k} (max 50)")
            clean_vals = []
            for val in vals:
                val = str(val).strip()
                if '"' in val or "'" in val or len(val) > 100:
                    raise HTTPException(400, f"Invalid value in dimension_in[{k}]: {val}")
                clean_vals.append(val)
            where.append(f"dimensions->>:key_in_{i} = ANY(:vals_in_{i})")
            params[f"key_in_{i}"] = k
            params[f"vals_in_{i}"] = clean_vals # type: ignore

    limit = min(request.limit, MAX_QUERY_RESULTS)
    params["limit"] = limit # type: ignore

    query = text(f"""
        SELECT timestamp, value, dimensions, tags
        FROM canonical_metrics
        WHERE {" AND ".join(where)}
        ORDER BY timestamp DESC
        LIMIT :limit
    """)

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            points = [
                DataPoint(
                    timestamp=row["timestamp"],
                    value=float(row["value"]),
                    dimensions=row["dimensions"] or {},
                    tags=row["tags"] or {}
                )
                for row in rows
            ]
            return DataQueryResponse(
                metric_name=request.metric_name,
                points=points,
                total=len(points)
            )
    except Exception as e:
        logger.exception("Query execution error")
        raise HTTPException(500, "Query failed")
```
### 📄 `api/routes/dimensions.py`

```python
# api/routes/dimensions.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import DimensionCreate, DimensionRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from config import mask_secrets

router = APIRouter(prefix="/dimensions", tags=["Dimensions"])


@router.post("/", response_model=DimensionRead, status_code=status.HTTP_201_CREATED)
def create_dimension(
    data: DimensionCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    try:
        dim_key = service.create_dimension(data, tenant_id=current_user.tenant_id)  # type: ignore
        dim = service.get_dimension(dim_key, tenant_id=current_user.tenant_id)
        if not dim:
            raise HTTPException(status_code=500, detail="Dimension created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "dimension", resource_id=dim_key)
        return dim
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[DimensionRead])
def list_dimensions(
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    return service.list_dimensions(tenant_id=current_user.tenant_id)


@router.get("/{dimension_key}", response_model=DimensionRead)
def get_dimension(
    dimension_key: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    dim = service.get_dimension(dimension_key, tenant_id=current_user.tenant_id)
    if not dim:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return dim

```
### 📄 `api/routes/forecasts.py`

```python
# api/routes/forecasts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from api.schemas import ForecastResponse, ForecastPoint
from api.auth import TokenData
from core.rbac import require_permission
from config import logger, mask_secrets

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get("/predict", response_model=ForecastResponse)
def predict_metric(
    metric_name: str = Query(...),
    horizon_hours: int = Query(24, ge=1, le=168),
    region: Optional[str] = Query(None),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    """Generate a forecast for a metric using the trained Prophet model.

    Returns predicted values with confidence intervals for the requested horizon.
    """
    from core.metadata_service import metadata_service

    valid_metrics = {m.metric_name for m in metadata_service.list_metrics(active_only=True)}
    if metric_name not in valid_metrics:
        raise HTTPException(404, f"Metric '{metric_name}' not found or inactive")

    dimensions: Dict[str, str] = {}
    if region:
        dimensions["region"] = region

    try:
        points = _generate_forecast(metric_name, dimensions, horizon_hours)
    except ImportError:
        raise HTTPException(501, "ML libraries not available for forecasting")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Forecast failed for {metric_name}: {mask_secrets(str(e))}")
        raise HTTPException(500, "Forecast generation failed")

    return ForecastResponse(
        metric_name=metric_name,
        dimensions=dimensions,
        horizon_hours=horizon_hours,
        points=points,
    )


def _generate_forecast(metric_name: str, dimensions: Dict[str, str], horizon_hours: int):
    """Try cached model first, fall back to fitting on recent data."""
    import pandas as pd
    import numpy as np

    try:
        from prophet import Prophet
    except ImportError:
        raise ImportError("Prophet is not installed")

    from core.database import get_engine
    from sqlalchemy import text
    from config import get_cache
    import joblib

    # Try to load a pre-trained model from cache
    group_key = "_".join(f"{k}={v}" for k, v in sorted(dimensions.items())) or "all"
    cache_key = f"ml_model:{metric_name}:{group_key}"
    cache = get_cache()
    model_bytes = cache.get(cache_key)
    model = None

    if model_bytes:
        try:
            model = joblib.loads(model_bytes)
        except Exception:
            model = None

    if model is None:
        # Fit a lightweight model on recent data
        engine = get_engine()
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)

        where = ["metric_name = :metric", "timestamp >= :cutoff"]
        params: dict = {"metric": metric_name, "cutoff": cutoff}

        if dimensions.get("region"):
            where.append("dimensions->>'region' = :region")
            params["region"] = dimensions["region"]

        query = text(f"""
            SELECT timestamp AS ds, value AS y
            FROM canonical_metrics
            WHERE {' AND '.join(where)}
            ORDER BY timestamp
            LIMIT 5000
        """)

        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()

        if len(rows) < 48:
            raise ValueError(f"Not enough data for forecast (need 48+, got {len(rows)})")

        df = pd.DataFrame(rows)
        df["ds"] = pd.to_datetime(df["ds"])
        if df["ds"].dt.tz is not None:
            df["ds"] = df["ds"].dt.tz_convert("UTC").dt.tz_localize(None)
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df = df.dropna().sort_values("ds").drop_duplicates(subset="ds", keep="last")

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.90,
        )
        import os, sys
        with open(os.devnull, "w") as devnull:
            old = sys.stdout
            sys.stdout = devnull
            try:
                model.fit(df)
            finally:
                sys.stdout = old

        # Cache the model for 24h
        try:
            cache.set(cache_key, joblib.dumps(model), ex=86400)
        except Exception:
            pass

    # Generate future dataframe
    future = model.make_future_dataframe(periods=horizon_hours, freq="h")
    forecast = model.predict(future)

    # Only return the future part
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    future_forecast = forecast[forecast["ds"] > now_naive].tail(horizon_hours)

    points = []
    for _, row in future_forecast.iterrows():
        ts = row["ds"].to_pydatetime().replace(tzinfo=timezone.utc)
        points.append(ForecastPoint(
            timestamp=ts,
            value=round(float(row["yhat"]), 4),
            lower=round(float(row["yhat_lower"]), 4),
            upper=round(float(row["yhat_upper"]), 4),
        ))

    return points

```
### 📄 `api/routes/incidents.py`

```python
# api/routes/incidents.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import text
from core.database import get_engine
from api.auth import get_current_user, TokenData
from core.rbac import require_permission
from api.schemas import (
    IncidentCreate, IncidentRead, IncidentStatusUpdate,
    IncidentAssign, IncidentCommentCreate, IncidentCommentRead,
    IncidentListResponse, SlaPolicyCreate, SlaPolicyRead,
)
from config import mask_secrets, logger
from core.audit import log_audit
from api.limiter import limiter

router = APIRouter(prefix="/incidents", tags=["Incidents"])

VALID_TRANSITIONS = {
    "new": {"in_progress", "escalated", "closed"},
    "in_progress": {"escalated", "resolved", "closed"},
    "escalated": {"in_progress", "resolved", "closed"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}

INCIDENT_COLUMNS = """
    id, alert_message, metric, region, value, priority, status, detected_at,
    assigned_to, started_at, resolved_at, closed_at, description, alert_event_id,
    response_deadline, resolution_deadline, response_breached, resolution_breached,
    escalation_level, last_escalated_at, external_id, external_system, external_url
"""


def _row_to_incident(row) -> IncidentRead:
    return IncidentRead(
        id=row["id"],
        alert_message=row["alert_message"],
        metric=row["metric"],
        region=row["region"],
        value=row["value"],
        priority=row["priority"],
        status=row["status"],
        detected_at=row["detected_at"],
        assigned_to=row["assigned_to"],
        started_at=row["started_at"],
        resolved_at=row["resolved_at"],
        closed_at=row["closed_at"],
        description=row["description"],
        alert_event_id=row["alert_event_id"],
        response_deadline=row["response_deadline"],
        resolution_deadline=row["resolution_deadline"],
        response_breached=row["response_breached"] or False,
        resolution_breached=row["resolution_breached"] or False,
        escalation_level=row["escalation_level"] or 0,
        last_escalated_at=row["last_escalated_at"],
        external_id=row.get("external_id"),
        external_system=row.get("external_system"),
        external_url=row.get("external_url"),
    )


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    breached: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    where = ["tenant_id = :tenant_id"]
    params = {"tenant_id": current_user.tenant_id, "limit": limit, "offset": offset}

    if status:
        where.append("status = :status")
        params["status"] = status
    if priority:
        where.append("priority = :priority")
        params["priority"] = priority
    if assigned_to:
        where.append("assigned_to = :assigned_to")
        params["assigned_to"] = assigned_to
    if metric:
        where.append("metric = :metric")
        params["metric"] = metric
    if breached is True:
        where.append("(response_breached = true OR resolution_breached = true)")

    where_clause = " AND ".join(where)
    engine = get_engine()

    try:
        with engine.connect() as conn:
            total = conn.execute(
                text(f"SELECT COUNT(*) FROM incidents WHERE {where_clause}"), params
            ).scalar()

            rows = conn.execute(
                text(f"""
                    SELECT {INCIDENT_COLUMNS}
                    FROM incidents WHERE {where_clause}
                    ORDER BY detected_at DESC LIMIT :limit OFFSET :offset
                """),
                params,
            ).mappings().all()

            return IncidentListResponse(
                items=[_row_to_incident(r) for r in rows],
                total=total,
            )
    except Exception as e:
        logger.exception("Error listing incidents")
        raise HTTPException(500, "Failed to list incidents")


@router.post("/", response_model=IncidentRead, status_code=201)
@limiter.limit("30/minute")
async def create_incident(
    request: Request,
    data: IncidentCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    now = datetime.now(timezone.utc)
    engine = get_engine()

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(f"""
                    INSERT INTO incidents (
                        alert_message, metric, region, value, priority, status,
                        detected_at, assigned_to, description, alert_event_id, tenant_id
                    ) VALUES (
                        :alert_message, :metric, :region, :value, :priority, 'new',
                        :detected_at, :assigned_to, :description, :alert_event_id, :tenant_id
                    )
                    RETURNING {INCIDENT_COLUMNS}
                """),
                {
                    "alert_message": data.alert_message,
                    "metric": data.metric,
                    "region": data.region,
                    "value": data.value,
                    "priority": data.priority,
                    "detected_at": now,
                    "assigned_to": data.assigned_to,
                    "description": data.description,
                    "alert_event_id": data.alert_event_id,
                    "tenant_id": current_user.tenant_id,
                },
            ).mappings().first()

        incident = _row_to_incident(row)

        # Apply SLA policy
        try:
            from core.sla_service import apply_sla_to_incident
            apply_sla_to_incident(incident.id, current_user.tenant_id, data.priority, now)
        except Exception as e:
            logger.warning(f"Failed to apply SLA: {e}")

        # Assign default escalation chain
        try:
            with engine.begin() as conn:
                chain = conn.execute(
                    text("""
                        SELECT id FROM escalation_chains
                        WHERE tenant_id = :tid AND is_active = true
                        ORDER BY created_at LIMIT 1
                    """),
                    {"tid": current_user.tenant_id},
                ).mappings().first()
                if chain:
                    conn.execute(
                        text("UPDATE incidents SET escalation_chain_id = :cid WHERE id = :id"),
                        {"cid": chain["id"], "id": incident.id},
                    )
        except Exception as e:
            logger.warning(f"Failed to assign escalation chain: {e}")

        log_audit(current_user.username, current_user.tenant_id, "create", "incident", resource_id=str(incident.id))

        # Push to i-doit
        try:
            from core.idoit_service import push_incident_create
            push_incident_create(incident.id)
        except Exception as e:
            logger.warning(f"i-doit push failed: {e}")

        # Re-read to get SLA + i-doit fields
        with engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id"),
                {"id": incident.id},
            ).mappings().first()
        return _row_to_incident(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating incident")
        raise HTTPException(500, "Failed to create incident")


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"""
                SELECT {INCIDENT_COLUMNS} FROM incidents
                WHERE id = :id AND tenant_id = :tid
            """),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

    if not row:
        raise HTTPException(404, "Incident not found")
    return _row_to_incident(row)


@router.patch("/{incident_id}/status", response_model=IncidentRead)
@limiter.limit("30/minute")
async def update_incident_status(
    request: Request,
    incident_id: int,
    data: IncidentStatusUpdate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

    if not row:
        raise HTTPException(404, "Incident not found")

    current_status = row["status"]
    if data.status not in VALID_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            400,
            f"Cannot transition from '{current_status}' to '{data.status}'. "
            f"Allowed: {VALID_TRANSITIONS.get(current_status, set())}",
        )

    updates = ["status = :new_status"]
    params = {"id": incident_id, "new_status": data.status}

    if data.status == "in_progress" and current_status == "new":
        updates.append("started_at = :now")
        params["now"] = now
    elif data.status == "resolved":
        updates.append("resolved_at = :now")
        params["now"] = now
    elif data.status == "closed":
        updates.append("closed_at = :now")
        params["now"] = now

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE incidents SET {', '.join(updates)} WHERE id = :id"),
            params,
        )

    # Add comment for status change
    if data.comment:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO incident_comments (incident_id, author, content)
                    VALUES (:iid, :author, :content)
                """),
                {"iid": incident_id, "author": current_user.username, "content": data.comment},
            )

    log_audit(
        current_user.username, current_user.tenant_id, "status_change", "incident",
        resource_id=str(incident_id),
        changes={"from": current_status, "to": data.status},
    )

    # Sync to i-doit
    try:
        from core.idoit_service import push_status_update
        push_status_update(incident_id, data.status)
    except Exception as e:
        logger.warning(f"i-doit status sync failed: {e}")

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id"),
            {"id": incident_id},
        ).mappings().first()
    return _row_to_incident(row)


@router.patch("/{incident_id}/assign", response_model=IncidentRead)
def assign_incident(
    incident_id: int,
    data: IncidentAssign,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

    if not exists:
        raise HTTPException(404, "Incident not found")

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE incidents SET assigned_to = :assigned_to WHERE id = :id"),
            {"id": incident_id, "assigned_to": data.assigned_to},
        )

    if data.comment:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO incident_comments (incident_id, author, content)
                    VALUES (:iid, :author, :content)
                """),
                {
                    "iid": incident_id,
                    "author": current_user.username,
                    "content": data.comment,
                },
            )

    log_audit(
        current_user.username, current_user.tenant_id, "assign", "incident",
        resource_id=str(incident_id),
        changes={"assigned_to": data.assigned_to},
    )

    # Sync to i-doit
    try:
        from core.idoit_service import push_assignment
        push_assignment(incident_id, data.assigned_to)
    except Exception as e:
        logger.warning(f"i-doit assign sync failed: {e}")

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id"),
            {"id": incident_id},
        ).mappings().first()
    return _row_to_incident(row)


@router.post("/{incident_id}/escalate", response_model=IncidentRead)
def escalate_incident(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    """Manually escalate an incident to the next level."""
    engine = get_engine()
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, escalation_level, escalation_chain_id, status
                FROM incidents WHERE id = :id AND tenant_id = :tid
            """),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).mappings().first()

    if not row:
        raise HTTPException(404, "Incident not found")
    if row["status"] in ("resolved", "closed"):
        raise HTTPException(400, "Cannot escalate resolved/closed incident")

    current_level = row["escalation_level"] or 0
    next_level_num = current_level + 1

    chain_id = row["escalation_chain_id"]
    if not chain_id:
        # Try to find default chain
        with engine.connect() as conn:
            chain = conn.execute(
                text("SELECT id FROM escalation_chains WHERE tenant_id = :tid AND is_active = true ORDER BY created_at LIMIT 1"),
                {"tid": current_user.tenant_id},
            ).mappings().first()
        if not chain:
            raise HTTPException(400, "No escalation chain configured")
        chain_id = chain["id"]

    with engine.connect() as conn:
        level_info = conn.execute(
            text("SELECT level, notify_role FROM escalation_levels WHERE chain_id = :cid AND level = :lvl"),
            {"cid": chain_id, "lvl": next_level_num},
        ).mappings().first()

    if not level_info:
        raise HTTPException(400, f"No escalation level {next_level_num} defined in chain")

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE incidents SET
                    escalation_level = :level,
                    escalation_chain_id = :chain_id,
                    status = 'escalated',
                    last_escalated_at = :now
                WHERE id = :id
            """),
            {"id": incident_id, "level": next_level_num, "chain_id": chain_id, "now": now},
        )

        conn.execute(
            text("""
                INSERT INTO incident_comments (incident_id, author, content)
                VALUES (:iid, :author, :content)
            """),
            {
                "iid": incident_id,
                "author": current_user.username,
                "content": f"Escalated to L{next_level_num} ({level_info['notify_role']})",
            },
        )

    log_audit(
        current_user.username, current_user.tenant_id, "escalate", "incident",
        resource_id=str(incident_id),
        changes={"from_level": current_level, "to_level": next_level_num},
    )

    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = :id"),
            {"id": incident_id},
        ).mappings().first()
    return _row_to_incident(row)


# --- Comments ---

@router.get("/{incident_id}/comments", response_model=List[IncidentCommentRead])
def list_comments(
    incident_id: int,
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

    if not exists:
        raise HTTPException(404, "Incident not found")

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, incident_id, author, content, created_at
                FROM incident_comments WHERE incident_id = :iid
                ORDER BY created_at ASC
            """),
            {"iid": incident_id},
        ).mappings().all()

    return [IncidentCommentRead(**r) for r in rows]


@router.post("/{incident_id}/comments", response_model=IncidentCommentRead, status_code=201)
def add_comment(
    incident_id: int,
    data: IncidentCommentCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": current_user.tenant_id},
        ).first()

    if not exists:
        raise HTTPException(404, "Incident not found")

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                INSERT INTO incident_comments (incident_id, author, content)
                VALUES (:iid, :author, :content)
                RETURNING id, incident_id, author, content, created_at
            """),
            {"iid": incident_id, "author": current_user.username, "content": data.content},
        ).mappings().first()

    # Sync comment to i-doit
    try:
        from core.idoit_service import push_comment
        push_comment(incident_id, current_user.username, data.content)
    except Exception as e:
        logger.warning(f"i-doit comment sync failed: {e}")

    return IncidentCommentRead(**row)


# --- SLA Policies ---

@router.get("/sla/policies", response_model=List[SlaPolicyRead])
def list_sla_policies(
    current_user: TokenData = Depends(require_permission("read:alerts")),
):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, tenant_id, name, priority, response_time_minutes,
                       resolution_time_minutes, escalation_after_minutes, is_active, created_at
                FROM sla_policies WHERE tenant_id = :tid ORDER BY priority
            """),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [SlaPolicyRead(**r) for r in rows]


@router.post("/sla/policies", response_model=SlaPolicyRead, status_code=201)
def create_sla_policy(
    data: SlaPolicyCreate,
    current_user: TokenData = Depends(require_permission("write:alerts")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO sla_policies (tenant_id, name, priority, response_time_minutes,
                                              resolution_time_minutes, escalation_after_minutes)
                    VALUES (:tid, :name, :priority, :resp, :res, :esc)
                    RETURNING id, tenant_id, name, priority, response_time_minutes,
                              resolution_time_minutes, escalation_after_minutes, is_active, created_at
                """),
                {
                    "tid": current_user.tenant_id,
                    "name": data.name,
                    "priority": data.priority,
                    "resp": data.response_time_minutes,
                    "res": data.resolution_time_minutes,
                    "esc": data.escalation_after_minutes,
                },
            ).mappings().first()
        log_audit(current_user.username, current_user.tenant_id, "create", "sla_policy", resource_id=str(row["id"]))
        return SlaPolicyRead(**row)
    except Exception as e:
        raise HTTPException(400, f"Failed to create SLA policy: {mask_secrets(str(e))}")

```
### 📄 `api/routes/metrics.py`

```python
# api/routes/metrics.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import MetricCreate, MetricRead, MetricUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.post("/", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
def create_metric(
    data: MetricCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    try:
        metric_name = service.create_metric(data, tenant_id=current_user.tenant_id)  # type: ignore
        metric = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
        if not metric:
            raise HTTPException(status_code=500, detail="Metric created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "metric", resource_id=metric_name)
        return metric
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[MetricRead])
def list_metrics(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    return service.list_metrics(active_only=active_only, tenant_id=current_user.tenant_id)


@router.get("/{metric_name}", response_model=MetricRead)
def get_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    metric = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.put("/{metric_name}", response_model=MetricRead)
def update_metric(
    metric_name: str,
    data: MetricUpdate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    if data.metric_name != metric_name:
        raise HTTPException(status_code=400, detail="Cannot change metric_name on update")

    try:
        service.create_metric(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = service.get_metric(metric_name, tenant_id=current_user.tenant_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Metric updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "metric", resource_id=metric_name)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:metrics")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM metadata_metrics WHERE metric_name = :name AND tenant_id = :tid"),
                {"name": metric_name, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Metric not found")
        service._invalidate_cache("metrics")
        log_audit(current_user.username, current_user.tenant_id, "delete", "metric", resource_id=metric_name)
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))

```
### 📄 `api/routes/ml_configs.py`

```python
# api/routes/ml_configs.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import MLConfigCreate, MLConfigRead
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/ml/configs", tags=["ML Configs"])


@router.post("/", response_model=MLConfigRead, status_code=status.HTTP_201_CREATED)
def create_ml_config(
    data: MLConfigCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    try:
        config_id = service.create_ml_config(data, tenant_id=current_user.tenant_id)  # type: ignore
        config = next((c for c in service.list_active_ml_configs(tenant_id=current_user.tenant_id) if c.id == config_id), None)
        if not config:
            raise HTTPException(status_code=500, detail="Config created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "ml_config", resource_id=str(config_id))
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[MLConfigRead])
def list_ml_configs(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:ml")),
):
    tid = current_user.tenant_id
    return service.list_active_ml_configs(tenant_id=tid) if active_only else service.list_all_ml_configs(tenant_id=tid)


@router.get("/{config_id}", response_model=MLConfigRead)
def get_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:ml")),
):
    configs = service.list_active_ml_configs(tenant_id=current_user.tenant_id)
    config = next((c for c in configs if c.id == config_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="ML config not found")
    return config


@router.put("/{config_id}", response_model=MLConfigRead)
def update_ml_config(
    config_id: UUID,
    data: MLConfigCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    try:
        service.create_ml_config(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = next((c for c in service.list_active_ml_configs(tenant_id=current_user.tenant_id) if c.id == config_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Config updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "ml_config", resource_id=str(config_id))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:ml")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_ml_configs SET is_active = false WHERE id = :id AND tenant_id = :tid"),
                {"id": config_id, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="ML config not found")
        service._invalidate_cache("ml_configs")
        log_audit(current_user.username, current_user.tenant_id, "delete", "ml_config", resource_id=str(config_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))

```
### 📄 `api/routes/rules.py`

```python
# api/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from api.schemas import RuleCreate, RuleRead, RuleUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: RuleCreate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        rule_id = service.create_rule(data, tenant_id=current_user.tenant_id)  # type: ignore
        rule = _get_rule_by_id(service, rule_id)
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        log_audit(current_user.username, current_user.tenant_id, "create", "rule", resource_id=str(rule_id))
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.get("/", response_model=List[RuleRead])
def list_rules(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rules = service.list_active_rules(tenant_id=current_user.tenant_id)
    if not active_only:
        rules = _list_all_rules(service, tenant_id=current_user.tenant_id)
    return rules


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("read:rules")),
):
    rule = _get_rule_by_id(service, rule_id, tenant_id=current_user.tenant_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    try:
        service.create_rule(data, tenant_id=current_user.tenant_id)  # type: ignore
        updated = _get_rule_by_id(service, rule_id, tenant_id=current_user.tenant_id)
        if not updated:
            raise HTTPException(status_code=500, detail="Rule updated but not found")
        log_audit(current_user.username, current_user.tenant_id, "update", "rule", resource_id=str(rule_id))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=mask_secrets(str(e)))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(require_permission("write:rules")),
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_rules SET is_active = false WHERE id = :id AND tenant_id = :tid"),
                {"id": rule_id, "tid": current_user.tenant_id},
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found")
        service._invalidate_cache("rules")
        log_audit(current_user.username, current_user.tenant_id, "delete", "rule", resource_id=str(rule_id))
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=mask_secrets(str(e)))


def _get_rule_by_id(service: MetadataService, rule_id: UUID, tenant_id: str = "default"):
    """Fetch a single rule by ID directly from DB."""
    engine = service._get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active,
                       created_at, updated_at
                FROM metadata_rules WHERE id = :id AND tenant_id = :tid
            """),
            {"id": rule_id, "tid": tenant_id},
        ).mappings().first()
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "condition": service._deserialize_json(row["condition"]),
        "labels": service._deserialize_json(row["labels"]),
        "actions": service._deserialize_json(row["actions"]),
        "is_active": row["is_active"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _list_all_rules(service: MetadataService, tenant_id: str = "default"):
    """List all rules including inactive ones."""
    engine = service._get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules WHERE tenant_id = :tid ORDER BY name
            """),
            {"tid": tenant_id},
        ).mappings().all()
    from core.metadata_service import RuleDTO
    return [
        RuleDTO(
            id=r["id"], name=r["name"], description=r["description"],
            condition=service._deserialize_json(r["condition"]),
            labels=service._deserialize_json(r["labels"]),
            actions=service._deserialize_json(r["actions"]),
            is_active=r["is_active"],
        )
        for r in rows
    ]

```
### 📄 `api/routes/webhooks.py`

```python
# api/routes/webhooks.py
"""
Webhook endpoints for external systems:
- /webhook/grafana → receive Grafana alerts → Telegram
- /webhook/idoit    → receive structured alerts → Telegram + i-doit incident
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import hmac
import requests
from config import settings, logger, mask_secrets
from core.notifications import notify
from api.limiter import limiter

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# === Схемы ===

class GrafanaAlert(BaseModel):
    title: str = Field(..., min_length=1)
    message: str = ""
    status: str = "firing"  # firing / resolved


class IdoitAlertData(BaseModel):
    title: str = Field(..., min_length=1, description="Краткое название алерта")
    message: str = Field(..., description="Детали")
    priority: str = Field("warning", pattern="^(info|warning|critical)$")
    region: Optional[str] = Field("N/A", description="Регион РФ, e.g. RU-MOW")
    metric: str = Field(..., description="Имя метрики, e.g. api_latency_p99")
    value: Optional[str] = Field("N/A", description="Текущее значение")

    @validator("region")
    def validate_region(cls, v):
        if v and len(v) > 20:
            raise ValueError("region too long")
        return v


# === Вспомогательные функции ===

def verify_webhook_key(request: Request) -> bool:
    key_header = request.headers.get("X-API-KEY")
    if not settings.WEBHOOK_API_KEY:
        logger.error("WEBHOOK_API_KEY not configured — rejecting all webhook requests")
        return False
    if not key_header:
        return False
    return hmac.compare_digest(key_header, settings.WEBHOOK_API_KEY)


def create_idoit_incident(alert_data: IdoitAlertData) -> Dict[str, Any]:
    if not (settings.I_DOIT_API_URL and settings.I_DOIT_API_KEY):
        logger.info("i-doit integration disabled (no URL or API key)")
        return {"success": False, "error": "i-doit disabled"}

    payload = {
        "jsonrpc": "2.0",
        "method": "cmdb.object.create",
        "params": {
            "apikey": settings.I_DOIT_API_KEY,
            "objTypeID": 10,  # Инцидент
            "title": f"[ALERT] {alert_data.title}",
            "properties": {
                "description": (
                    f"{alert_data.message}\n"
                    f"Регион: {alert_data.region}\n"
                    f"Метрика: {alert_data.metric}\n"
                    f"Значение: {alert_data.value}"
                ),
                "status": "2",           # Open
                "priority": "3",          # High
                "assigned": "admin"
            }
        },
        "id": 1
    }

    try:
        resp = requests.post(
            settings.I_DOIT_API_URL,
            json=payload,
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("error"):
            err_msg = result["error"].get("message", "unknown")
            logger.error(f"i-doit API error: {err_msg}")
            return {"success": False, "error": err_msg}

        obj_id = result.get("result", {}).get("objectID")
        if not obj_id:
            logger.error("i-doit: no objectID in response")
            return {"success": False, "error": "no objectID"}

        logger.info(f"✅ i-doit incident created: {obj_id}")
        return {"success": True, "id": obj_id}

    except requests.RequestException as e:
        logger.exception("i-doit request failed")
        return {"success": False, "error": f"connection error: {mask_secrets(str(e))}"}
    except Exception as e:
        logger.exception("i-doit processing error")
        return {"success": False, "error": mask_secrets(str(e))}


# === Роуты ===

@router.post("/grafana", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def grafana_webhook(
    request: Request,
    payload: GrafanaAlert
):
    if not verify_webhook_key(request):
        logger.warning(f"Invalid X-API-KEY from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    priority = "critical" if payload.status == "firing" else "info"
    message = f"🚨 {payload.title}\n{payload.message}"
    notify(message, priority)
    return {"status": "ok", "sent": True}


@router.post("/idoit", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def idoit_webhook(
    request: Request,
    payload: IdoitAlertData
):
    # 🔐 Аутентификация
    if not verify_webhook_key(request):
        logger.warning(f"Invalid X-API-KEY from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    # ✅ Уведомление в Telegram
    telegram_msg = f"🚨 i-doit: {payload.title}\n{payload.message}"
    notify(telegram_msg, payload.priority)

    # 🛠️ Создание инцидента в i-doit (если настроено)
    result = create_idoit_incident(payload)
    if not result["success"]:
        # Не фейлим запрос — логируем, но продолжаем
        logger.warning(f"i-doit incident creation failed: {result['error']}")

    return {
        "success": True,
        "telegram_sent": True,
        "idoit": result
    }


# === i-doit inbound sync: status/assignment changes pushed back to us ===

class IdoitSyncPayload(BaseModel):
    """Payload sent by i-doit when an incident is updated."""
    object_id: str = Field(..., description="i-doit object ID")
    status: Optional[str] = Field(None, description="i-doit status code")
    assigned: Optional[str] = Field(None, description="Assigned user")
    comment: Optional[str] = Field(None, description="Logbook comment")


@router.post("/idoit/sync", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def idoit_sync_webhook(request: Request, payload: IdoitSyncPayload):
    """
    Inbound webhook from i-doit.
    Receives status/assignment updates and syncs them back to local incidents.
    Configure i-doit to POST here on incident state changes.
    """
    if not verify_webhook_key(request):
        raise HTTPException(status_code=403, detail="Invalid API key")

    from core.database import get_engine
    from sqlalchemy import text as sa_text

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            sa_text("SELECT id, status FROM incidents WHERE external_id = :eid"),
            {"eid": payload.object_id},
        ).mappings().first()

    if not row:
        logger.warning(f"i-doit sync: no local incident for object_id={payload.object_id}")
        raise HTTPException(404, "Incident not found for this external_id")

    incident_id = row["id"]
    result = {"incident_id": incident_id, "synced": []}

    if payload.status:
        from core.idoit_service import pull_status_update
        pull_status_update(incident_id, payload.status, payload.assigned)
        result["synced"].append("status")

    if payload.comment:
        with engine.begin() as conn:
            conn.execute(
                sa_text("""
                    INSERT INTO incident_comments (incident_id, author, content)
                    VALUES (:iid, :author, :content)
                """),
                {"iid": incident_id, "author": f"i-doit:{payload.assigned or 'system'}", "content": payload.comment},
            )
        result["synced"].append("comment")

    # Audit log for external sync
    try:
        from core.audit import log_audit
        log_audit(
            f"idoit:{payload.assigned or 'system'}", "default",
            "sync", "incident",
            resource_id=str(incident_id),
            changes={"synced": result.get("synced", [])},
        )
    except Exception:
        pass

    return {"success": True, **result}
```
### 📄 `api/routes/websocket.py`

```python
# api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import List
import json
from config import logger
from api.auth import verify_token
from core.pubsub import subscribe_alerts

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


async def alert_stream_task():
    """Subscribe to Redis Pub/Sub and broadcast alerts to WebSocket clients."""
    await subscribe_alerts(manager.broadcast)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

```
### 📄 `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline
on:
  push:
    branches:
      - main
      - master
  pull_request:
    types: [opened, synchronize]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install lint tools
        run: |
          pip install --upgrade pip
          pip install ruff
      - name: Run linter (Ruff)
        run: ruff check . --ignore E501

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      TESTING: "1"
      SECRET_KEY: test-secret-key-for-ci
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: testpass
      POSTGRES_SERVER: localhost
      POSTGRES_PORT: "5432"
      POSTGRES_DB: test_db
      DATABASE_URL: postgresql://postgres:testpass@localhost:5432/test_db
      REDIS_HOST: localhost
      REDIS_PORT: "6379"
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: "$2b$12$LJ3m4ys5qOzXkVzKlGT..ea.J7GIIO0C.jPBsCijMOZqMPfTpF8a6"
      I_DOIT_API_KEY: test-key
      I_DOIT_API_URL: http://localhost/api
      WEBHOOK_API_KEY: test-webhook-key
      KAFKA_ENABLED: "false"
      CLICKHOUSE_ENABLED: "false"
      LDAP_ENABLED: "false"
      OIDC_ENABLED: "false"
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short -x --ignore=tests/test_ml.py
      - name: Upload coverage
        if: always()
        run: |
          python -m pytest tests/ --ignore=tests/test_ml.py --cov=api --cov=core --cov-report=term-missing || true

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
      - name: Build and push image
        run: |
          docker build -t Maarkh/sit_center:latest -f Dockerfile .
          docker push Maarkh/sit_center:latest

```
### 📄 `.github/workflows/generate-docs.yml`

```yaml
name: Generate Project Documentation
on:
  push:
    branches:
      - master  # или любая другая нужная тебе ветка
    paths:
      - "**.py"
      - ".gitignore"
      - "requirements.txt"
      - "generate_docs.py"
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Generate documentation
        run: |
          python generate_docs.py
      - name: Commit and Push Changes
        run: |
          git config --local user.email "m.a.arkhipov@gmail.com"
          git config --local user.name "Maarkh"
          git add README.md
          git diff-index --quiet HEAD || git commit -m "docs: auto-update project structure"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
### 📄 `docs/disaster-recovery.md`

```markdown
# Disaster Recovery Plan

## Architecture Overview

- **API**: 2 instances behind nginx (least_conn)
- **Database**: TimescaleDB primary + streaming replica
- **Cache**: Redis with 3 Sentinel nodes for automatic failover
- **Message Queue**: Kafka with configurable replication factor

## RTO / RPO Targets

| Component    | RPO           | RTO           |
|-------------|---------------|---------------|
| PostgreSQL  | ~0 (sync rep) | < 5 min       |
| Redis       | < 1 min       | < 30 sec      |
| Kafka       | 0 (acks=all)  | < 2 min       |
| API         | N/A           | < 30 sec      |

## Backup Procedures

### PostgreSQL / TimescaleDB

1. **Continuous WAL archiving** (recommended):
   ```bash
   # pg_basebackup for full backup
   pg_basebackup -h db -U $POSTGRES_USER -D /backups/base -Ft -z -P

   # WAL archiving configured in postgresql.conf
   archive_mode = on
   archive_command = 'cp %p /backups/wal/%f'
   ```

2. **Scheduled pg_dump** (supplementary):
   ```bash
   # Daily logical backup
   pg_dump -h db -U $POSTGRES_USER $POSTGRES_DB | gzip > /backups/daily/$(date +%Y%m%d).sql.gz
   ```

3. **Retention**: Keep 7 daily, 4 weekly, 12 monthly backups.

### Redis

- Redis Sentinel handles automatic failover.
- RDB snapshots every 60 seconds (if >1000 keys changed).
- AOF enabled for durability.

### Kafka

- Topic replication factor >= 2 in production.
- Consumer offsets committed after successful processing.

## Failover Steps

### Database Failover

1. Sentinel or monitoring detects primary failure.
2. Promote replica: `pg_ctl promote -D /var/lib/postgresql/data`
3. Update connection strings (or use PgBouncer / HAProxy for transparent failover).
4. Rebuild old primary as new replica.

### Redis Failover

1. Redis Sentinel automatically elects new master.
2. Application uses Sentinel-aware connection (no manual intervention needed).

### API Failover

1. nginx health checks detect failed instance.
2. Traffic automatically routed to healthy instance.
3. Restart or replace failed instance.

## Recovery Testing

- Test failover quarterly.
- Restore from backup to a test environment monthly.
- Document and review results.

```
### 📄 `alembic/env.py`

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from config import get_database_url

# Импорт Base и моделей (создадим чуть позже)
from core.models import Base

# Настройка логов
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем URL БД
database_url = os.getenv("DATABASE_URL") or get_database_url()
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), # type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Отслеживает изменения типов (например, VARCHAR(50) → VARCHAR(100))
            render_as_batch=True  # Для поддержки SQLite (и улучшения миграций в PostgreSQL)
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```
### 📄 `alembic/versions/001_add_admin_dashboard.py`

```python
"""Add admin dashboard tables

Revision ID: add_admin_dashboard_001
Revises: 
Create Date: 2025-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_admin_dashboard_001'
down_revision = None  # Или ID предыдущей миграции
branch_labels = None
depends_on = None


def upgrade():
    """
    Создание таблиц для админ-панели конструктора дашбордов
    """
    
    # 1. Таблица конфигураций дашбордов
    op.create_table(
        'dashboard_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('updated_at', sa.String(), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('theme', sa.String(length=50), default='light'),
        sa.Column('auto_refresh_interval', sa.Integer(), default=30),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 2. Таблица виджетов
    op.create_table(
        'widget_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('metric_column', sa.String(length=100), nullable=False),
        sa.Column('position_x', sa.Integer(), default=0),
        sa.Column('position_y', sa.Integer(), default=0),
        sa.Column('width', sa.Integer(), default=6),
        sa.Column('height', sa.Integer(), default=4),
        sa.Column('time_filter', sa.String(length=10), default='1h'),
        sa.Column('aggregation', sa.String(length=50), default='sum'),
        sa.Column('group_by', sa.String(length=100), nullable=True),
        sa.Column('chart_config', sa.JSON(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_visible', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboard_configs.id'], ondelete='CASCADE')
    )
    
    # Индексы для widget_configs
    op.create_index('ix_widget_dashboard_id', 'widget_configs', ['dashboard_id'])
    op.create_index('ix_widget_order', 'widget_configs', ['order'])
    
    # 3. Таблица слоёв карты
    op.create_table(
        'map_layer_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('metric_column', sa.String(length=100), nullable=False),
        sa.Column('color_scale', sa.String(length=50), default='Reds'),
        sa.Column('opacity', sa.Float(), default=0.7),
        sa.Column('show_in_rotation', sa.Boolean(), default=True),
        sa.Column('rotation_order', sa.Integer(), default=0),
        sa.Column('legend_title', sa.String(length=100), nullable=True),
        sa.Column('value_format', sa.String(length=50), default='{:.0f}'),
        sa.Column('thresholds', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для map_layer_configs
    op.create_index('ix_map_layer_rotation_order', 'map_layer_configs', ['rotation_order'])
    op.create_index('ix_map_layer_active', 'map_layer_configs', ['is_active'])
    
    # 4. Таблица тем
    op.create_table(
        'theme_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('primary_color', sa.String(length=7), default='#007BFF'),
        sa.Column('secondary_color', sa.String(length=7), default='#6C757D'),
        sa.Column('background_color', sa.String(length=7), default='#FFFFFF'),
        sa.Column('text_color', sa.String(length=7), default='#212529'),
        sa.Column('chart_colors', sa.JSON(), nullable=True),
        sa.Column('font_family', sa.String(length=100), default='Arial, sans-serif'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    print("✅ Таблицы админ-панели созданы")


def downgrade():
    """
    Удаление таблиц админ-панели
    """
    op.drop_table('theme_configs')
    op.drop_index('ix_map_layer_active', 'map_layer_configs')
    op.drop_index('ix_map_layer_rotation_order', 'map_layer_configs')
    op.drop_table('map_layer_configs')
    op.drop_index('ix_widget_order', 'widget_configs')
    op.drop_index('ix_widget_dashboard_id', 'widget_configs')
    op.drop_table('widget_configs')
    op.drop_table('dashboard_configs')
    
    print("✅ Таблицы админ-панели удалены")
```
### 📄 `alembic/versions/002_add_metadata_ml_configs.py`

```python
"""add metadata_ml_configs table

Revision ID: 002_add_ml_configs
Revises: 001_add_admin_dashboard
Create Date: 2025-11-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_ml_configs'
down_revision = '001_add_admin_dashboard'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metadata_ml_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('group_by', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('methods', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('method_params', postgresql.JSONB(), nullable=False),
        sa.Column('retrain_schedule', sa.String(), nullable=True),
        sa.Column('auto_alert', sa.Boolean(), nullable=True),
        sa.Column('alert_severity', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['metric_name'], ['metadata_metrics.metric_name'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_ml_configs_metric', 'metadata_ml_configs', ['metric_name'])
    op.create_index('ix_ml_configs_active', 'metadata_ml_configs', ['is_active'])


def downgrade():
    op.drop_table('metadata_ml_configs')
```
### 📄 `k8s/sit-center/Chart.yaml`

```yaml
apiVersion: v2
name: sit-center
description: Situational Center — enterprise monitoring platform
version: 1.0.0
appVersion: "1.0.0"
type: application
keywords:
  - monitoring
  - observability
  - aiops
  - situational-center

```
### 📄 `k8s/sit-center/values.yaml`

```yaml
# Default values for sit-center Helm chart

replicaCount:
  api: 2
  celeryWorker: 2
  mlWorker: 1
  celeryBeat: 1

image:
  repository: situational-center/api
  tag: latest
  pullPolicy: IfNotPresent

# -- External secrets (create manually or via ExternalSecrets operator)
existingSecret: sit-center-secrets
# Keys expected in secret:
#   POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY,
#   ADMIN_PASSWORD, WEBHOOK_API_KEY, I_DOIT_API_KEY

postgresql:
  host: sit-center-postgresql
  port: 5432
  user: sit_center
  database: sit_center

redis:
  host: sit-center-redis
  port: 6379

# -- Optional components
kafka:
  enabled: false
  bootstrapServers: sit-center-kafka:9092

clickhouse:
  enabled: false
  host: sit-center-clickhouse
  port: 8123

ldap:
  enabled: false
  url: "ldap://ldap:389"
  baseDn: ""

oidc:
  enabled: false
  issuerUrl: ""
  clientId: ""
  baseUrl: "https://sit-center.example.com"

# -- Resource limits
resources:
  api:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 1Gi
  celeryWorker:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 1Gi
  mlWorker:
    requests:
      cpu: 500m
      memory: 2Gi
    limits:
      cpu: "2"
      memory: 4Gi

# -- Autoscaling
autoscaling:
  api:
    enabled: true
    minReplicas: 2
    maxReplicas: 8
    targetCPUUtilizationPercentage: 70

# -- Ingress
ingress:
  enabled: true
  className: nginx
  host: sit-center.example.com
  tls: true
  secretName: sit-center-tls

# -- Service
service:
  type: ClusterIP
  port: 8000

# -- Monitoring
prometheus:
  scrape: true
  port: 8000
  path: /metric

# -- Vault integration (optional)
vault:
  enabled: false
  address: "https://vault.example.com"
  role: sit-center
  secretPath: secret/data/sit-center

```
### 📄 `k8s/sit-center/templates/api-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-api
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
    app.kubernetes.io/component: api
spec:
  replicas: {{ .Values.replicaCount.api }}
  selector:
    matchLabels:
      {{- include "sit-center.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: api
  template:
    metadata:
      labels:
        {{- include "sit-center.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: api
      annotations:
        {{- if .Values.prometheus.scrape }}
        prometheus.io/scrape: "true"
        prometheus.io/port: {{ .Values.prometheus.port | quote }}
        prometheus.io/path: {{ .Values.prometheus.path }}
        {{- end }}
        {{- if .Values.vault.enabled }}
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
        vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
        {{- end }}
    spec:
      containers:
        - name: api
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 8000
              name: http
          env:
            {{- include "sit-center.env" . | nindent 12 }}
          resources:
            {{- toYaml .Values.resources.api | nindent 12 }}
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 20
            periodSeconds: 30
          startupProbe:
            httpGet:
              path: /health
              port: http
            failureThreshold: 10
            periodSeconds: 5

```
### 📄 `k8s/sit-center/templates/celery-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-celery-worker
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
    app.kubernetes.io/component: celery-worker
spec:
  replicas: {{ .Values.replicaCount.celeryWorker }}
  selector:
    matchLabels:
      {{- include "sit-center.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: celery-worker
  template:
    metadata:
      labels:
        {{- include "sit-center.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: celery-worker
    spec:
      containers:
        - name: worker
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command:
            - celery
            - -A
            - tasks.celery_app
            - worker
            - --loglevel=INFO
            - --concurrency=2
            - --max-tasks-per-child=100
          env:
            {{- include "sit-center.env" . | nindent 12 }}
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@{{ .Values.redis.host }}:{{ .Values.redis.port }}/0"
          resources:
            {{- toYaml .Values.resources.celeryWorker | nindent 12 }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-celery-beat
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
    app.kubernetes.io/component: celery-beat
spec:
  replicas: {{ .Values.replicaCount.celeryBeat }}
  selector:
    matchLabels:
      {{- include "sit-center.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: celery-beat
  template:
    metadata:
      labels:
        {{- include "sit-center.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: celery-beat
    spec:
      containers:
        - name: beat
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command:
            - celery
            - -A
            - tasks.celery_app
            - beat
            - --loglevel=INFO
          env:
            {{- include "sit-center.env" . | nindent 12 }}
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@{{ .Values.redis.host }}:{{ .Values.redis.port }}/0"
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 250m
              memory: 512Mi

```
### 📄 `k8s/sit-center/templates/hpa.yaml`

```yaml
{{- if .Values.autoscaling.api.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Release.Name }}-api
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .Release.Name }}-api
  minReplicas: {{ .Values.autoscaling.api.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.api.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.api.targetCPUUtilizationPercentage }}
{{- end }}

```
### 📄 `k8s/sit-center/templates/ingress.yaml`

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-ingress
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/websocket-services: {{ .Release.Name }}-api
spec:
  ingressClassName: {{ .Values.ingress.className }}
  {{- if .Values.ingress.tls }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ .Values.ingress.secretName }}
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-api
                port:
                  number: {{ .Values.service.port }}
{{- end }}

```
### 📄 `k8s/sit-center/templates/ml-worker-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-ml-worker
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
    app.kubernetes.io/component: ml-worker
spec:
  replicas: {{ .Values.replicaCount.mlWorker }}
  selector:
    matchLabels:
      {{- include "sit-center.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: ml-worker
  template:
    metadata:
      labels:
        {{- include "sit-center.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: ml-worker
    spec:
      containers:
        - name: ml-worker
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command:
            - celery
            - -A
            - celery_app
            - worker
            - --queues=ml
            - --loglevel=INFO
            - --concurrency=1
            - --max-tasks-per-child=10
          env:
            {{- include "sit-center.env" . | nindent 12 }}
            - name: REDIS_URL
              value: "redis://:$(REDIS_PASSWORD)@{{ .Values.redis.host }}:{{ .Values.redis.port }}/0"
          resources:
            {{- toYaml .Values.resources.mlWorker | nindent 12 }}

```
### 📄 `k8s/sit-center/templates/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-api
  labels:
    {{- include "sit-center.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "sit-center.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: api

```
### 📄 `tests/__init__.py`

```python

```
### 📄 `tests/conftest.py`

```python
# tests/conftest.py
import os
os.environ["TESTING"] = "1"

import pytest
import fakeredis
from unittest.mock import patch, MagicMock
from celery_app import celery_app


@pytest.fixture(autouse=True, scope="session")
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield


@pytest.fixture()
def fake_redis_instance():
    """A standalone fakeredis instance for direct use in tests."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def mock_redis(fake_redis_instance):
    """Patch get_redis / get_cache globally so no real Redis is needed."""
    with patch("config.get_redis", return_value=fake_redis_instance), \
         patch("config.get_cache", return_value=fake_redis_instance):
        yield fake_redis_instance


@pytest.fixture()
def api_client():
    """FastAPI TestClient with mocked dependencies."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    """Return valid Authorization headers for admin user."""
    from api.auth import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={
            "sub": "testadmin",
            "scopes": ["admin"],
            "tenant_id": "default",
            "roles": ["admin"],
            "permissions": [
                "read:metrics", "write:metrics", "read:rules", "write:rules",
                "read:alerts", "write:alerts", "read:ml", "write:ml",
                "admin:tenants", "admin:users", "read:audit",
            ],
        },
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_auth_headers():
    """Return valid Authorization headers for viewer user (read-only)."""
    from api.auth import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={
            "sub": "testviewer",
            "scopes": [],
            "tenant_id": "default",
            "roles": ["viewer"],
            "permissions": ["read:metrics", "read:rules", "read:alerts"],
        },
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}

```
### 📄 `tests/test_admin_api.py`

```python
# tests/test_admin_api.py
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


def _mock_engine_with_rows(rows):
    """Create a mock engine whose connect().execute() returns rows."""
    engine = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    conn = MagicMock()
    conn.execute.return_value = result
    engine.connect.return_value.__enter__ = lambda s: conn
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


def _mock_engine_for_write(returning_row=None):
    """Create a mock engine whose begin().execute() returns a row (for INSERT RETURNING)."""
    engine = MagicMock()
    conn = MagicMock()
    if returning_row:
        result = MagicMock()
        result.mappings.return_value.first.return_value = returning_row
        conn.execute.return_value = result
    engine.begin.return_value.__enter__ = lambda s: conn
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return engine


# --- Tenants ---

def test_list_tenants(api_client, auth_headers):
    rows = [{"id": "default", "name": "Default", "is_active": True}]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/tenants", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "default"


def test_create_tenant(api_client, auth_headers):
    engine = _mock_engine_for_write()
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/tenants",
            json={"id": "new_tenant", "name": "New Tenant"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["id"] == "new_tenant"


def test_create_tenant_invalid_id(api_client, auth_headers):
    response = api_client.post(
        "/admin/tenants",
        json={"id": "invalid tenant!", "name": "Bad"},
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- Users ---

def test_list_users(api_client, auth_headers):
    uid = str(uuid4())
    rows = [
        {"id": uid, "username": "alice", "email": "alice@example.com",
         "tenant_id": "default", "is_active": True, "auth_provider": "local"}
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/users?tenant_id=default", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "alice"


def test_create_user(api_client, auth_headers):
    uid = str(uuid4())
    row = {
        "id": uid, "username": "bob", "email": "bob@test.com",
        "tenant_id": "default", "is_active": True, "auth_provider": "local",
    }
    engine = _mock_engine_for_write(returning_row=row)
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/users",
            json={"username": "bob", "email": "bob@test.com"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["username"] == "bob"


# --- Roles ---

def test_list_roles(api_client, auth_headers):
    rid = str(uuid4())
    rows = [
        {"id": rid, "name": "viewer", "tenant_id": "default",
         "permissions": ["read:metrics"], "description": "Read-only"}
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/roles?tenant_id=default", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["name"] == "viewer"


def test_create_role(api_client, auth_headers):
    rid = str(uuid4())
    row = {
        "id": rid, "name": "editor", "tenant_id": "default",
        "permissions": ["read:metrics", "write:metrics"], "description": "Editor",
    }
    engine = _mock_engine_for_write(returning_row=row)
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/roles",
            json={"name": "editor", "permissions": ["read:metrics", "write:metrics"]},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["name"] == "editor"


# --- User-Role assignment ---

def test_assign_role(api_client, auth_headers):
    engine = _mock_engine_for_write()
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/user-roles",
            json={"user_id": str(uuid4()), "role_id": str(uuid4())},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["status"] == "ok"


def test_unassign_role(api_client, auth_headers):
    engine = _mock_engine_for_write()
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.request(
            "DELETE",
            "/admin/user-roles",
            json={"user_id": str(uuid4()), "role_id": str(uuid4())},
            headers=auth_headers,
        )
    assert response.status_code == 204


# --- Auth required ---

def test_admin_endpoints_require_auth(api_client):
    endpoints = ["/admin/tenants", "/admin/users", "/admin/roles"]
    for ep in endpoints:
        response = api_client.get(ep)
        assert response.status_code == 401, f"{ep} should require auth"


def test_admin_endpoints_require_admin_role(api_client, viewer_auth_headers):
    response = api_client.get("/admin/tenants", headers=viewer_auth_headers)
    assert response.status_code == 403

```
### 📄 `tests/test_alerts_logic.py`

```python
# tests/test_alerts_logic.py
import pytest
from core.alerts import generate_alert_hash, is_steady_increase


def test_generate_alert_hash():
    h = generate_alert_hash("cpu", "Moscow", 42.0)
    assert isinstance(h, str)
    assert len(h) == 32


def test_generate_alert_hash_deterministic():
    h1 = generate_alert_hash("cpu", "Moscow", 42.0)
    h2 = generate_alert_hash("cpu", "Moscow", 42.0)
    assert h1 == h2


def test_generate_alert_hash_different_inputs():
    h1 = generate_alert_hash("cpu", "Moscow", 42.0)
    h2 = generate_alert_hash("cpu", "SPb", 42.0)
    assert h1 != h2


def test_is_steady_increase_true():
    assert is_steady_increase([1, 2, 3]) is True
    assert is_steady_increase([10, 20, 30, 40]) is True


def test_is_steady_increase_false():
    assert is_steady_increase([3, 2, 1]) is False
    assert is_steady_increase([1, 3, 2]) is False
    assert is_steady_increase([1, 2]) is False  # less than 3 elements


def test_alert_suppression(fake_redis_instance):
    from core.alerts import suppress_alert, is_alert_suppressed
    suppress_alert("test_hash", 60)
    assert is_alert_suppressed("test_hash") is True


def test_alert_not_suppressed(fake_redis_instance):
    from core.alerts import is_alert_suppressed
    assert is_alert_suppressed("nonexistent_hash") is False

```
### 📄 `tests/test_api_alerts.py`

```python
# tests/test_api_alerts.py
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture
def mock_db_engine():
    with patch("api.routes.alerts.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield engine


def test_list_alerts_empty(api_client, auth_headers, mock_db_engine):
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.all.return_value = []

    response = api_client.get("/alerts/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_alert_not_found(api_client, auth_headers, mock_db_engine):
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.first.return_value = None

    alert_id = uuid4()
    response = api_client.get(f"/alerts/{alert_id}", headers=auth_headers)
    assert response.status_code == 404


def test_list_alerts_with_data(api_client, auth_headers, mock_db_engine):
    alert_id = uuid4()
    now = datetime.now(timezone.utc)
    row = {
        "id": alert_id,
        "rule_id": None,
        "ml_config_id": None,
        "metric_name": "complaints",
        "dimensions": {"region": "Moscow"},
        "value": 42.0,
        "event_time": now,
        "detected_at": now,
        "status": "firing",
        "sent": True,
        "fingerprint": "abc123",
    }
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.all.return_value = [row]

    response = api_client.get("/alerts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["metric_name"] == "complaints"

```
### 📄 `tests/test_api_data.py`

```python
# tests/test_api_data.py
import pytest
from unittest.mock import patch, MagicMock
from core.metadata_service import MetricDTO


def test_prometheus_label_values_name(api_client, auth_headers):
    with patch("api.routes.data.get_engine") as mock_engine:
        conn = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value = [("metric_a",), ("metric_b",)]

        response = api_client.get("/data/prometheus/api/v1/label/__name__/values", headers=auth_headers)
        assert response.status_code == 200
        assert "metric_a" in response.json()


def test_prometheus_label_values_forbidden_dimension(api_client, auth_headers):
    response = api_client.get("/data/prometheus/api/v1/label/forbidden_dim/values", headers=auth_headers)
    assert response.status_code == 403


def test_query_range_invalid_step(api_client, auth_headers):
    mock_metrics = [MetricDTO(metric_name="test_metric", display_name="Test", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "test_metric",
                "start": 1000000,
                "end": 1000100,
                "step": "invalid",
            },
            headers=auth_headers,
        )
    assert response.status_code == 400


def test_query_range_sql_injection_step(api_client, auth_headers):
    mock_metrics = [MetricDTO(metric_name="test_metric", display_name="Test", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "test_metric",
                "start": 1000000,
                "end": 1000100,
                "step": "1s; DROP TABLE--",
            },
            headers=auth_headers,
        )
    assert response.status_code == 400

```
### 📄 `tests/test_api_metrics.py`

```python
# tests/test_api_metrics.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from core.metadata_service import MetricDTO


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def test_list_metrics(api_client, auth_headers, mock_metadata_service):
    now = datetime.now()
    mock_metric = MagicMock()
    mock_metric.metric_name = "test_metric"
    mock_metric.display_name = "Test Metric"
    mock_metric.description = "A test metric"
    mock_metric.unit = "count"
    mock_metric.default_threshold = None
    mock_metric.default_critical_threshold = None
    mock_metric.is_active = True
    mock_metric.created_at = now
    mock_metric.updated_at = now
    mock_metadata_service.list_metrics.return_value = [mock_metric]
    response = api_client.get("/metrics/?active_only=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["metric_name"] == "test_metric"


def test_get_metric_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_metric.return_value = None
    response = api_client.get("/metrics/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_create_metric(api_client, auth_headers, mock_metadata_service):
    now = datetime.now()
    mock_metadata_service.create_metric.return_value = "new_metric"
    mock_metric = MagicMock()
    mock_metric.metric_name = "new_metric"
    mock_metric.display_name = "New Metric"
    mock_metric.description = None
    mock_metric.unit = ""
    mock_metric.default_threshold = None
    mock_metric.default_critical_threshold = None
    mock_metric.is_active = True
    mock_metric.created_at = now
    mock_metric.updated_at = now
    mock_metadata_service.get_metric.return_value = mock_metric
    response = api_client.post(
        "/metrics/",
        json={
            "metric_name": "new_metric",
            "display_name": "New Metric",
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["metric_name"] == "new_metric"

```
### 📄 `tests/test_api_versioning.py`

```python
# tests/test_api_versioning.py
"""Test that API v1 prefix routes work alongside legacy routes."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_metadata_service():
    with patch("api.routes.metrics.get_metadata_service") as mock:
        service = MagicMock()
        mock.return_value = service
        service.list_metrics.return_value = []
        yield service


class TestApiVersioning:
    def test_health_no_prefix(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_metrics_v1_prefix(self, api_client, auth_headers, mock_metadata_service):
        resp = api_client.get("/api/v1/metrics/", headers=auth_headers)
        assert resp.status_code == 200

    def test_metrics_legacy_prefix(self, api_client, auth_headers, mock_metadata_service):
        resp = api_client.get("/metrics/", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.routes.alerts.get_engine")
    def test_alerts_v1_prefix(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/api/v1/alerts/", headers=auth_headers)
        assert resp.status_code == 200

```
### 📄 `tests/test_api_webhooks.py`

```python
# tests/test_api_webhooks.py
import pytest
from unittest.mock import patch


def test_grafana_webhook_no_api_key(api_client):
    response = api_client.post(
        "/webhooks/grafana",
        json={"title": "Test Alert", "message": "body", "status": "firing"},
    )
    assert response.status_code == 403


def test_grafana_webhook_invalid_api_key(api_client):
    response = api_client.post(
        "/webhooks/grafana",
        json={"title": "Test Alert", "message": "body", "status": "firing"},
        headers={"X-API-KEY": "wrong_key"},
    )
    assert response.status_code == 403


def test_grafana_webhook_valid(api_client):
    from config import settings
    with patch("api.routes.webhooks.notify") as mock_notify:
        response = api_client.post(
            "/webhooks/grafana",
            json={"title": "Test Alert", "message": "body", "status": "firing"},
            headers={"X-API-KEY": settings.WEBHOOK_API_KEY},
        )
        assert response.status_code == 200
        mock_notify.assert_called_once()


def test_idoit_webhook_valid(api_client):
    from config import settings
    with patch("api.routes.webhooks.notify"), \
         patch("api.routes.webhooks.create_idoit_incident", return_value={"success": True, "id": 1}):
        response = api_client.post(
            "/webhooks/idoit",
            json={
                "title": "Test",
                "message": "details",
                "priority": "warning",
                "metric": "cpu",
                "region": "Moscow",
            },
            headers={"X-API-KEY": settings.WEBHOOK_API_KEY},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

```
### 📄 `tests/test_audit_api.py`

```python
# tests/test_audit_api.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def _mock_engine_with_rows(rows):
    engine = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    conn = MagicMock()
    conn.execute.return_value = result
    engine.connect.return_value.__enter__ = lambda s: conn
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


def test_get_audit_logs(api_client, auth_headers):
    rows = [
        {
            "id": 1,
            "username": "admin",
            "tenant_id": "default",
            "action": "create",
            "resource_type": "metric",
            "resource_id": "cpu_usage",
            "changes": {},
            "ip_address": "127.0.0.1",
            "timestamp": datetime.now(),
        }
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.audit.get_engine", return_value=engine):
        response = api_client.get("/audit/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["action"] == "create"


def test_audit_logs_filter_by_action(api_client, auth_headers):
    engine = _mock_engine_with_rows([])
    with patch("api.routes.audit.get_engine", return_value=engine):
        response = api_client.get(
            "/audit/logs?action=login&resource_type=session",
            headers=auth_headers,
        )
    assert response.status_code == 200


def test_audit_logs_require_auth(api_client):
    response = api_client.get("/audit/logs")
    assert response.status_code == 401


def test_audit_logs_require_read_audit_permission(api_client, viewer_auth_headers):
    response = api_client.get("/audit/logs", headers=viewer_auth_headers)
    assert response.status_code == 403

```
### 📄 `tests/test_auth_oidc.py`

```python
# tests/test_auth_oidc.py
import pytest
from unittest.mock import patch


def test_oidc_login_disabled(api_client):
    response = api_client.get("/auth/login/oidc", follow_redirects=False)
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]


def test_oidc_callback_disabled(api_client):
    response = api_client.get("/auth/callback/oidc")
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]

```
### 📄 `tests/test_auth_strategies.py`

```python
# tests/test_auth_strategies.py
"""Tests for the decomposed auth strategies (core/auth_strategies.py)."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestEnvAdminAuth:
    def test_valid_env_admin(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = "$2b$12$hash"
            mock_pwd.verify.return_value = True

            token = try_env_admin_auth("admin", "password123")
            assert isinstance(token, str)
            assert len(token) > 0

    def test_wrong_username(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.ADMIN_USERNAME = "admin"

            with pytest.raises(HTTPException) as exc_info:
                try_env_admin_auth("wrong_user", "password123")
            assert exc_info.value.status_code == 401

    def test_wrong_password(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = "$2b$12$hash"
            mock_pwd.verify.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                try_env_admin_auth("admin", "wrong_pass")
            assert exc_info.value.status_code == 401


class TestDbAuth:
    def test_db_user_found(self):
        from core.auth_strategies import try_db_auth

        mock_user_row = {
            "id": 1,
            "username": "dbuser",
            "password_hash": "$2b$12$hash",
            "tenant_id": "tenant1",
            "is_active": True,
            "roles": ["viewer"],
            "permissions": ["read:metrics"],
        }

        with patch("core.database.get_engine") as mock_engine, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = mock_user_row
            mock_pwd.verify.return_value = True

            result = try_db_auth("dbuser", "password")
            assert result is not None
            assert result["username"] == "dbuser"
            assert result["tenant_id"] == "tenant1"
            assert "token" in result

    def test_db_user_not_found(self):
        from core.auth_strategies import try_db_auth

        with patch("core.database.get_engine") as mock_engine:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = None

            result = try_db_auth("nonexistent", "password")
            assert result is None

    def test_db_wrong_password_raises(self):
        from core.auth_strategies import try_db_auth

        mock_user_row = {
            "id": 1,
            "username": "dbuser",
            "password_hash": "$2b$12$hash",
            "tenant_id": "tenant1",
            "is_active": True,
            "roles": [],
            "permissions": [],
        }

        with patch("core.database.get_engine") as mock_engine, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = mock_user_row
            mock_pwd.verify.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                try_db_auth("dbuser", "wrong_pass")
            assert exc_info.value.status_code == 401


class TestLdapAuth:
    def test_ldap_disabled_returns_none(self):
        from core.auth_strategies import try_ldap_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.LDAP_ENABLED = False
            result = try_ldap_auth("user", "pass")
            assert result is None

    def test_ldap_auth_failure_returns_none(self):
        from core.auth_strategies import try_ldap_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.LDAP_ENABLED = True

            with patch("core.ldap_auth.ldap_authenticator") as mock_ldap:
                mock_ldap.authenticate.return_value = None
                result = try_ldap_auth("user", "wrong_pass")
                assert result is None

```
### 📄 `tests/test_data_routes.py`

```python
# tests/test_data_routes.py
"""Tests for data query routes: Prometheus compat, analytics, and query endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from api.routes.data import _parse_duration, safe_jsonb_eq, validate_label_name
from fastapi import HTTPException


class TestParseDuration:
    def test_valid_seconds(self):
        assert _parse_duration("15s") == 15

    def test_valid_minutes(self):
        assert _parse_duration("5m") == 300

    def test_valid_hours(self):
        assert _parse_duration("2h") == 7200

    def test_valid_days(self):
        assert _parse_duration("1d") == 86400

    def test_invalid_format(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("abc")
        assert exc_info.value.status_code == 400

    def test_too_large_step(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("2d")
        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail

    def test_too_long_string(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("12345678901")
        assert exc_info.value.status_code == 400

    def test_zero_step(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("0s")
        assert exc_info.value.status_code == 400


class TestValidateLabelName:
    def test_valid_label(self):
        assert validate_label_name("region") == "region"

    def test_valid_underscore_start(self):
        assert validate_label_name("_private") == "_private"

    def test_invalid_special_chars(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_label_name("region;DROP")
        assert exc_info.value.status_code == 400

    def test_too_long(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_label_name("a" * 51)
        assert exc_info.value.status_code == 400


class TestSafeJsonbEq:
    def test_valid_key_value(self):
        expr, params = safe_jsonb_eq("dimensions", "f0", "region", "Moscow")
        assert "key_f0" in params
        assert "val_f0" in params
        assert params["key_f0"] == "region"
        assert params["val_f0"] == "Moscow"

    def test_invalid_key_raises(self):
        with pytest.raises(Exception):
            safe_jsonb_eq("dimensions", "f0", "region;DROP", "Moscow")

    def test_forbidden_chars_in_value(self):
        with pytest.raises(HTTPException):
            safe_jsonb_eq("dimensions", "f0", "region", 'Mos"cow')


class TestPrometheusEndpoints:
    @patch("api.routes.data.get_engine")
    def test_label_values_requires_auth(self, mock_engine, api_client):
        resp = api_client.get("/data/prometheus/api/v1/label/__name__/values")
        assert resp.status_code in (401, 403)

    @patch("api.routes.data.get_engine")
    def test_label_values_with_auth(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value = [("cpu_usage",), ("memory_used",)]

        resp = api_client.get(
            "/data/prometheus/api/v1/label/__name__/values",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    @patch("api.routes.data.get_engine")
    def test_disallowed_dimension_label(self, mock_engine, api_client, auth_headers):
        resp = api_client.get(
            "/data/prometheus/api/v1/label/secret_field/values",
            headers=auth_headers,
        )
        assert resp.status_code == 403

```
### 📄 `tests/test_dimensions_api.py`

```python
# tests/test_dimensions_api.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_dim(key="region", desc="Region dimension"):
    m = MagicMock()
    m.dimension_key = key
    m.description = desc
    m.allowed_values = ["RU-MOW", "RU-SPE"]
    m.is_required = False
    m.created_at = datetime.now()
    return m


def test_list_dimensions(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_dimensions.return_value = [_make_dim()]
    response = api_client.get("/dimensions/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dimension_key"] == "region"


def test_get_dimension(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_dimension.return_value = _make_dim("service", "Service dim")
    response = api_client.get("/dimensions/service", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["dimension_key"] == "service"


def test_get_dimension_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_dimension.return_value = None
    response = api_client.get("/dimensions/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_create_dimension(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.create_dimension.return_value = "env"
    mock_metadata_service.get_dimension.return_value = _make_dim("env", "Environment")

    response = api_client.post(
        "/dimensions/",
        json={"dimension_key": "env", "description": "Environment", "is_required": False},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["dimension_key"] == "env"


def test_create_dimension_invalid_key(api_client, auth_headers, mock_metadata_service):
    response = api_client.post(
        "/dimensions/",
        json={"dimension_key": "bad key!", "description": "Invalid"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_dimensions_require_auth(api_client):
    response = api_client.get("/dimensions/")
    assert response.status_code == 401

```
### 📄 `tests/test_forecasts_api.py`

```python
# tests/test_forecasts_api.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_forecast_deps():
    """Mock metadata_service that's imported locally inside forecast route."""
    mock_service = MagicMock()
    with patch("core.metadata_service.metadata_service", mock_service):
        yield mock_service


def _make_metric(name="cpu_usage"):
    m = MagicMock()
    m.metric_name = name
    return m


def test_forecast_metric_not_found(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = []
    response = api_client.get(
        "/forecasts/predict?metric_name=nonexistent&horizon_hours=24",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_forecast_ml_not_available(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    with patch("api.routes.forecasts._generate_forecast", side_effect=ImportError("No prophet")):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage",
            headers=auth_headers,
        )
    assert response.status_code == 501


def test_forecast_not_enough_data(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    with patch("api.routes.forecasts._generate_forecast",
               side_effect=ValueError("Not enough data")):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage",
            headers=auth_headers,
        )
    assert response.status_code == 400


def test_forecast_success(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    from api.schemas import ForecastPoint
    points = [
        ForecastPoint(
            timestamp=datetime.now(timezone.utc),
            value=42.5,
            lower=38.0,
            upper=47.0,
        )
    ]

    with patch("api.routes.forecasts._generate_forecast", return_value=points):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage&horizon_hours=12&region=RU-MOW",
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["metric_name"] == "cpu_usage"
    assert data["horizon_hours"] == 12
    assert len(data["points"]) == 1
    assert data["dimensions"]["region"] == "RU-MOW"


def test_forecast_requires_auth(api_client):
    response = api_client.get("/forecasts/predict?metric_name=x")
    assert response.status_code == 401

```
### 📄 `tests/test_idoit_service.py`

```python
# tests/test_idoit_service.py
"""Tests for i-doit service — push/pull operations."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_engine():
    with patch("core.idoit_service.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        yield engine, conn


class TestIsEnabled:
    def test_enabled_when_both_set(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = "key123"
            assert is_enabled() is True

    def test_disabled_when_no_url(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = ""
            s.I_DOIT_API_KEY = "key123"
            assert is_enabled() is False

    def test_disabled_when_no_key(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = ""
            assert is_enabled() is False


class TestStatusMapping:
    def test_status_to_idoit(self):
        from core.idoit_service import STATUS_TO_IDOIT
        assert STATUS_TO_IDOIT["new"] == "1"
        assert STATUS_TO_IDOIT["resolved"] == "3"
        assert STATUS_TO_IDOIT["closed"] == "4"

    def test_status_from_idoit(self):
        from core.idoit_service import STATUS_FROM_IDOIT
        assert STATUS_FROM_IDOIT["1"] == "new"
        assert STATUS_FROM_IDOIT["3"] == "resolved"

    def test_priority_mapping(self):
        from core.idoit_service import PRIORITY_TO_IDOIT, PRIORITY_FROM_IDOIT
        assert PRIORITY_TO_IDOIT["critical"] == "1"
        assert PRIORITY_FROM_IDOIT["1"] == "critical"


class TestPushIncidentCreate:
    def test_skips_when_disabled(self, mock_engine):
        from core.idoit_service import push_incident_create
        with patch("core.idoit_service.is_enabled", return_value=False):
            result = push_incident_create(1)
            assert result is None

    @patch("core.idoit_service.requests.post")
    def test_creates_incident_success(self, mock_post, mock_engine):
        engine, conn = mock_engine
        conn.execute.return_value.mappings.return_value.first.return_value = {
            "id": 1,
            "alert_message": "Test alert",
            "description": None,
            "metric": "cpu_usage",
            "region": "RU-MOW",
            "value": "95",
            "priority": "critical",
            "assigned_to": None,
            "status": "new",
        }

        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {
            "result": {"id": "42", "objectID": "42"}
        }

        from core.idoit_service import push_incident_create
        with patch("core.idoit_service.is_enabled", return_value=True), \
             patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = "key123"
            result = push_incident_create(1)
            assert result == "42"


class TestPullStatusUpdate:
    def test_pull_valid_status(self, mock_engine):
        engine, conn = mock_engine
        from core.idoit_service import pull_status_update

        with patch("core.idoit_service._log_sync"):
            pull_status_update(1, "3")  # 3 = resolved

        # Should have executed an UPDATE
        conn.execute.assert_called()

    def test_pull_unknown_status_ignored(self, mock_engine):
        engine, conn = mock_engine
        from core.idoit_service import pull_status_update

        with patch("core.idoit_service._log_sync"):
            pull_status_update(1, "99")

        # begin() should not be called for unknown status
        engine.begin.assert_not_called()

```
### 📄 `tests/test_incidents.py`

```python
# tests/test_incidents.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_db_engine():
    with patch("api.routes.incidents.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield engine


def _make_incident_row(overrides=None):
    row = {
        "id": 1,
        "alert_message": "High latency",
        "metric": "api_latency_p99",
        "region": "RU-MOW",
        "value": "500",
        "priority": "critical",
        "status": "new",
        "detected_at": datetime.now(timezone.utc),
        "assigned_to": None,
        "started_at": None,
        "resolved_at": None,
        "closed_at": None,
        "description": None,
        "alert_event_id": None,
        "response_deadline": None,
        "resolution_deadline": None,
        "response_breached": False,
        "resolution_breached": False,
        "escalation_level": 0,
        "last_escalated_at": None,
        "external_id": None,
        "external_system": None,
        "external_url": None,
    }
    if overrides:
        row.update(overrides)
    return row


def _setup_conn(engine, return_value):
    """Set up context-managed connection mock."""
    conn = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return conn


class TestListIncidents:
    def test_list_incidents_empty(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 0
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/incidents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_incidents_with_filters(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 1
        conn.execute.return_value.mappings.return_value.all.return_value = [
            _make_incident_row({"status": "in_progress"})
        ]

        resp = api_client.get(
            "/incidents/?status=in_progress&priority=critical",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_list_incidents_breached_filter(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 0
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/incidents/?breached=true", headers=auth_headers)
        assert resp.status_code == 200


class TestCreateIncident:
    @patch("api.routes.incidents.log_audit")
    def test_create_incident(self, mock_audit, api_client, auth_headers, mock_db_engine):
        row = _make_incident_row()
        conn = _setup_conn(mock_db_engine, row)
        conn.execute.return_value.mappings.return_value.first.return_value = row

        with patch("core.sla_service.apply_sla_to_incident"), \
             patch("core.idoit_service.push_incident_create", return_value=None):
            resp = api_client.post(
                "/incidents/",
                json={
                    "alert_message": "High latency",
                    "metric": "api_latency_p99",
                    "region": "RU-MOW",
                    "priority": "critical",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        assert resp.json()["alert_message"] == "High latency"


class TestGetIncident:
    def test_get_incident_found(self, api_client, auth_headers, mock_db_engine):
        row = _make_incident_row()
        conn = _setup_conn(mock_db_engine, row)
        conn.execute.return_value.mappings.return_value.first.return_value = row

        resp = api_client.get("/incidents/1", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_incident_not_found(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.mappings.return_value.first.return_value = None

        resp = api_client.get("/incidents/999", headers=auth_headers)
        assert resp.status_code == 404


class TestStatusTransitions:
    def test_valid_transition(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        # First call: check current status
        conn.execute.return_value.mappings.return_value.first.side_effect = [
            {"status": "new"},  # SELECT status
            _make_incident_row({"status": "in_progress"}),  # SELECT after update
        ]

        with patch("api.routes.incidents.log_audit"), \
             patch("core.idoit_service.push_status_update"):
            resp = api_client.patch(
                "/incidents/1/status",
                json={"status": "in_progress"},
                headers=auth_headers,
            )
        assert resp.status_code == 200

    def test_invalid_transition_closed_to_new(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.mappings.return_value.first.return_value = {"status": "closed"}

        resp = api_client.patch(
            "/incidents/1/status",
            json={"status": "new"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Cannot transition" in resp.json()["detail"]


class TestAssignIncident:
    def test_assign_success(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.first.return_value = (1,)
        conn.execute.return_value.mappings.return_value.first.return_value = _make_incident_row(
            {"assigned_to": "ops-user"}
        )

        with patch("api.routes.incidents.log_audit"), \
             patch("core.idoit_service.push_assignment"):
            resp = api_client.patch(
                "/incidents/1/assign",
                json={"assigned_to": "ops-user"},
                headers=auth_headers,
            )
        assert resp.status_code == 200

    def test_assign_not_found(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.first.return_value = None

        resp = api_client.patch(
            "/incidents/1/assign",
            json={"assigned_to": "ops-user"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

```
### 📄 `tests/test_mask_secrets.py`

```python
# tests/test_mask_secrets.py
from config import mask_secrets

def test_mask_bot_token():
    s = "token here bot123:ABCdefGHIjkLMNOP12345 rest"
    out = mask_secrets(s)
    assert "bot123:***" in out
    assert "ABCdefGHIjkLMNOP12345" not in out

def test_mask_redis_url():
    s = "redis://user:mysecret@redis:6379/0"
    out = mask_secrets(s)
    assert "redis://user:***@redis:6379/0" in out
    assert "mysecret" not in out

```
### 📄 `tests/test_mask_secrets_edge.py`

```python
# tests/test_mask_secrets_edge.py
"""
Edge-case tests for mask_secrets() — covering formats that reviewers flagged.
"""
from config import mask_secrets


# --- Redis URL edge cases ---

def test_mask_redis_password_only():
    """redis://:password@host (no username)"""
    s = "redis://:SuperSecret123@redis:6379/0"
    out = mask_secrets(s)
    assert "SuperSecret123" not in out
    assert "redis://:***@redis:6379/0" in out


def test_mask_redis_with_username():
    """redis://user:password@host"""
    s = "redis://default:mypass@redis:6379/0"
    out = mask_secrets(s)
    assert "mypass" not in out
    assert "redis://default:***@redis:6379/0" in out


def test_mask_redis_sentinel_url():
    """redis-sentinel://:pass@host"""
    s = "redis://:sentinel_pass@sentinel1:26379/0"
    out = mask_secrets(s)
    assert "sentinel_pass" not in out


def test_mask_redis_empty_password():
    """redis://:@host (empty password) should not crash"""
    s = "redis://:@redis:6379/0"
    out = mask_secrets(s)
    assert "redis://" in out


# --- PostgreSQL URL edge cases ---

def test_mask_postgres_standard():
    s = "postgresql://admin:p4ssw0rd@db:5432/mydb"
    out = mask_secrets(s)
    assert "p4ssw0rd" not in out
    assert "postgresql://admin:***@db:5432/mydb" in out


def test_mask_postgres_special_chars_in_password():
    """Password with special chars: @, :, /, #"""
    s = "postgresql://user:p%40ss%3Aw0rd@db:5432/mydb"
    out = mask_secrets(s)
    assert "p%40ss%3Aw0rd" not in out


def test_mask_postgres_no_username():
    s = "postgres://:secret@db:5432/mydb"
    out = mask_secrets(s)
    assert "secret" not in out


# --- Telegram bot token ---

def test_mask_telegram_token_standard():
    s = "bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz_0123456789"
    out = mask_secrets(s)
    assert "bot123456789:***" in out
    assert "ABCdefGHIjklMNOpqrsTUVwxyz_0123456789" not in out


def test_mask_telegram_token_in_url():
    s = "https://api.telegram.org/bot123456:ABCdef/sendMessage"
    out = mask_secrets(s)
    assert "ABCdef" not in out


# --- JSON key-value pairs ---

def test_mask_json_password():
    s = '{"password": "hunter2"}'
    out = mask_secrets(s)
    assert "hunter2" not in out


def test_mask_json_token():
    s = '{"token": "abc123xyz"}'
    out = mask_secrets(s)
    assert "abc123xyz" not in out


def test_mask_json_secret_key():
    s = "{'secret': 'my_secret_value'}"
    out = mask_secrets(s)
    assert "my_secret_value" not in out


# --- Generic key=value pairs ---

def test_mask_password_equals():
    s = "connection failed password=MySecret123 at host"
    out = mask_secrets(s)
    assert "MySecret123" not in out
    assert "password=***" in out


def test_mask_token_equals():
    s = "token=xoxb-123-456-abc other stuff"
    out = mask_secrets(s)
    assert "xoxb-123-456-abc" not in out


def test_mask_secret_equals():
    s = "SECRET=very_secret_value"
    out = mask_secrets(s)
    assert "very_secret_value" not in out


# --- Edge cases ---

def test_mask_none_input():
    assert mask_secrets(None) == ""


def test_mask_non_string_input():
    result = mask_secrets(12345)
    assert result == "12345"


def test_mask_empty_string():
    assert mask_secrets("") == ""


def test_mask_no_secrets():
    s = "This is a normal log message without any secrets"
    assert mask_secrets(s) == s


def test_mask_multiple_secrets_in_one_string():
    s = "DB: postgresql://user:dbpass@db:5432/mydb Redis: redis://:redispass@redis:6379"
    out = mask_secrets(s)
    assert "dbpass" not in out
    assert "redispass" not in out
    assert "***" in out


def test_mask_preserves_non_secret_content():
    s = "Error connecting to postgresql://admin:secret@db:5432/app — retrying in 5s"
    out = mask_secrets(s)
    assert "secret" not in out
    assert "Error connecting to" in out
    assert "retrying in 5s" in out

```
### 📄 `tests/test_metadata_service.py`

```python
# tests/test_metadata_service.py
import pytest
from unittest.mock import patch, MagicMock
from core.metadata_service import MetadataService, MetricDTO


@pytest.fixture
def service(fake_redis_instance):
    with patch("core.metadata_service.get_cache", return_value=fake_redis_instance), \
         patch("core.metadata_service.get_database_url", return_value="postgresql://test:test@localhost/test"):
        svc = MetadataService()
        svc._cache = fake_redis_instance
        yield svc


def test_make_fingerprint():
    fp = MetadataService.make_fingerprint("cpu", {"region": "Moscow"})
    assert isinstance(fp, str)
    assert len(fp) == 32  # md5 hex digest


def test_make_fingerprint_deterministic():
    fp1 = MetadataService.make_fingerprint("cpu", {"a": "1", "b": "2"})
    fp2 = MetadataService.make_fingerprint("cpu", {"b": "2", "a": "1"})
    assert fp1 == fp2


def test_list_metrics_cached(service, fake_redis_instance):
    import json
    cached = [{"metric_name": "m1", "display_name": "M1", "is_active": True, "unit": "", "description": None, "default_threshold": None, "default_critical_threshold": None}]
    fake_redis_instance.set("metadata:metrics:default:active", json.dumps(cached))

    result = service.list_metrics(active_only=True)
    assert len(result) == 1
    assert result[0].metric_name == "m1"


def test_serialize_deserialize(service):
    data = {"key": "value", "list": [1, 2, 3]}
    serialized = service._serialize_json(data)
    deserialized = service._deserialize_json(serialized)
    assert deserialized == data


def test_deserialize_none(service):
    assert service._deserialize_json(None) is None

```
### 📄 `tests/test_ml.py`

```python
# tests/test_ml.py
import pytest
from core.ml_anomaly import detect_anomaly_prophet_isolation_group
import pandas as pd

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=50, freq="H"),
        "value": [i + (10 if i % 10 == 0 else 0) for i in range(50)]  # С аномалиями
    })

def test_detect_anomaly_prophet(sample_df):
    anomalies = detect_anomaly_prophet_isolation_group(sample_df, dimensions={"region": "test"})
    assert len(anomalies) > 0
    assert "timestamp" in anomalies[0]
```
### 📄 `tests/test_ml_configs_api.py`

```python
# tests/test_ml_configs_api.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_config(config_id=None, name="test-config"):
    m = MagicMock()
    m.id = config_id or uuid4()
    m.name = name
    m.metric_name = "cpu_usage"
    m.group_by = ["region"]
    m.methods = ["prophet"]
    m.method_params = {}
    m.retrain_schedule = "0 3 * * *"
    m.auto_alert = True
    m.alert_severity = "warning"
    m.is_active = True
    m.created_at = datetime.now()
    m.updated_at = datetime.now()
    return m


def test_list_ml_configs(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config()]
    response = api_client.get("/ml/configs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-config"


def test_list_ml_configs_all(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_all_ml_configs.return_value = [_make_config()]
    response = api_client.get("/ml/configs/?active_only=false", headers=auth_headers)
    assert response.status_code == 200
    mock_metadata_service.list_all_ml_configs.assert_called_once()


def test_get_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config(cfg_id)]
    response = api_client.get(f"/ml/configs/{cfg_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "test-config"


def test_get_ml_config_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_active_ml_configs.return_value = []
    response = api_client.get(f"/ml/configs/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_create_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_metadata_service.create_ml_config.return_value = cfg_id
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config(cfg_id, "new-cfg")]

    response = api_client.post(
        "/ml/configs/",
        json={
            "name": "new-cfg",
            "metric_name": "cpu_usage",
            "methods": ["prophet"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "new-cfg"


def test_delete_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_engine = MagicMock()
    conn = MagicMock()
    result = MagicMock()
    result.rowcount = 1
    conn.execute.return_value = result
    mock_engine.begin.return_value.__enter__ = lambda s: conn
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    mock_metadata_service._get_engine.return_value = mock_engine

    response = api_client.delete(f"/ml/configs/{cfg_id}", headers=auth_headers)
    assert response.status_code == 204


def test_ml_configs_require_auth(api_client):
    response = api_client.get("/ml/configs/")
    assert response.status_code == 401

```
### 📄 `tests/test_ml_smoke.py`

```python
# tests/test_ml_smoke.py
"""
ML smoke tests that work WITHOUT heavy ML dependencies (Prophet, TensorFlow, torch).
These run in CI to verify ML pipeline logic, error handling, and graceful degradation.

Note: We do NOT import core.ml_anomaly directly because it pulls in tensorflow/torch
at module level. Instead, we test through the Celery task layer (which uses local
imports) and mock the ML internals.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from uuid import uuid4


# --- ML task layer (safe to import — uses lazy local imports) ---

def test_ml_tasks_import():
    """Verify ml_tasks module has expected Celery tasks."""
    from core.ml_tasks import run_ml_anomaly_check, retrain_ml_models, evaluate_rules_task
    assert callable(run_ml_anomaly_check)
    assert callable(retrain_ml_models)
    assert callable(evaluate_rules_task)


def test_run_ml_anomaly_check_handles_import_error():
    """ML anomaly check task gracefully handles missing ML libs."""
    from core.ml_tasks import run_ml_anomaly_check
    # ml_tasks does `from core.ml_anomaly import find_recent_ml_anomalies` inside the function.
    # We mock at the sys.modules level to simulate import failure.
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(side_effect=ImportError("No prophet"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        assert result == 0


def test_run_ml_anomaly_check_handles_runtime_error():
    """ML anomaly check task returns 0 on runtime failure."""
    from core.ml_tasks import run_ml_anomaly_check
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(side_effect=RuntimeError("DB down"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        assert result == 0


def test_run_ml_anomaly_check_success():
    """ML anomaly check returns anomaly list on success."""
    from core.ml_tasks import run_ml_anomaly_check
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(return_value=[{"id": 1}])
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        # The task calls find_recent_ml_anomalies and returns its result
        assert result is not None


def test_retrain_ml_models_handles_error():
    """Retrain task returns error status on failure."""
    from core.ml_tasks import retrain_ml_models
    mock_module = MagicMock()
    mock_module.retrain_all_models = MagicMock(side_effect=RuntimeError("DB down"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = retrain_ml_models()
        assert result["status"] == "error"
        assert "DB down" in result["message"]


def test_retrain_ml_models_success():
    """Retrain task returns success on happy path."""
    from core.ml_tasks import retrain_ml_models
    mock_module = MagicMock()
    mock_module.retrain_all_models = MagicMock()
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = retrain_ml_models()
        assert result["status"] == "success"


def test_evaluate_rules_task_handles_error():
    """Rule evaluation task returns error on failure."""
    from core.ml_tasks import evaluate_rules_task
    mock_re_module = MagicMock()
    mock_re_module.rule_engine.evaluate_all_rules.side_effect = RuntimeError("boom")
    with patch.dict("sys.modules", {"core.rule_engine": mock_re_module}):
        result = evaluate_rules_task()
        assert "error" in result


def test_evaluate_rules_task_success():
    """Rule evaluation returns check/fired counts."""
    from core.ml_tasks import evaluate_rules_task
    mock_result = MagicMock()
    mock_result.fired = True
    mock_result.rule_name = "test"
    mock_result.metric_name = "cpu"
    mock_result.operator = ">"
    mock_result.threshold = 80
    mock_result.current_value = 95.0

    mock_re_module = MagicMock()
    mock_re_module.rule_engine.evaluate_all_rules.return_value = [mock_result]
    with patch.dict("sys.modules", {"core.rule_engine": mock_re_module}), \
         patch("core.notifications.notify"):
        result = evaluate_rules_task()
        assert result["checked"] == 1
        assert result["fired"] == 1


# --- MLConfigDTO structure ---

def test_ml_config_dto_structure():
    """Verify MLConfigDTO has required fields."""
    from core.metadata_service import MLConfigDTO
    cfg = MLConfigDTO(
        name="test",
        metric_name="cpu_usage",
        group_by=["region"],
        methods=["prophet"],
        method_params={},
        retrain_schedule="0 3 * * *",
        auto_alert=True,
        alert_severity="warning",
        is_active=True,
        id=uuid4(),
    )
    assert cfg.metric_name == "cpu_usage"
    assert "prophet" in cfg.methods
    assert cfg.auto_alert is True


def test_ml_config_dto_defaults():
    """MLConfigDTO with minimal + default fields."""
    from core.metadata_service import MLConfigDTO
    cfg = MLConfigDTO(
        name="minimal",
        metric_name="m",
        group_by=[],
        methods=["prophet"],
        method_params={},
    )
    assert cfg.is_active is True
    assert cfg.group_by == []
    assert cfg.alert_severity == "warning"


# --- Anomaly serialization ---

def test_serialize_anomalies_empty():
    """serialize_anomalies works for empty list."""
    from core.utils import serialize_anomalies
    result = serialize_anomalies([])
    assert result is not None


def test_serialize_anomalies_with_data():
    """serialize_anomalies works for non-empty list."""
    from core.utils import serialize_anomalies
    anomaly = {
        "metric_name": "cpu",
        "timestamp": datetime.now(timezone.utc),
        "value": 42.5,
        "predicted": 40.0,
        "residual": 2.5,
    }
    result = serialize_anomalies([anomaly])
    assert result is not None


# --- Forecast endpoint (ML consumer) ---

def test_forecast_endpoint_handles_import_error(api_client, auth_headers):
    """Forecast returns 501 when ML libs are unavailable."""
    mock_svc = MagicMock()
    mock_metric = MagicMock()
    mock_metric.metric_name = "test_metric"
    mock_svc.list_metrics.return_value = [mock_metric]

    with patch("core.metadata_service.metadata_service", mock_svc), \
         patch("api.routes.forecasts._generate_forecast", side_effect=ImportError("No prophet")):
        resp = api_client.get("/forecasts/predict?metric_name=test_metric", headers=auth_headers)
    assert resp.status_code == 501


# --- ML config API (consumer of ML metadata) ---

def test_ml_configs_endpoint_returns_list(api_client, auth_headers):
    """GET /ml/configs/ returns a list (may be empty)."""
    from api.main import app
    from api.dependencies import get_metadata_service
    mock_svc = MagicMock()
    mock_svc.list_active_ml_configs.return_value = []
    app.dependency_overrides[get_metadata_service] = lambda: mock_svc
    try:
        resp = api_client.get("/ml/configs/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.pop(get_metadata_service, None)

```
### 📄 `tests/test_pubsub.py`

```python
# tests/test_pubsub.py
import pytest
from unittest.mock import patch, MagicMock
from core.pubsub import publish_alert, ALERT_CHANNEL
import json


def test_publish_alert_calls_redis():
    mock_redis = MagicMock()
    with patch("core.pubsub.redis.from_url", return_value=mock_redis):
        data = {"type": "alert", "metric": "cpu", "value": 99.0}
        publish_alert(data)
        mock_redis.publish.assert_called_once_with(
            ALERT_CHANNEL,
            json.dumps(data, ensure_ascii=False, default=str),
        )
        mock_redis.close.assert_called_once()


def test_publish_alert_handles_error():
    with patch("core.pubsub.redis.from_url", side_effect=Exception("connection failed")):
        # Should not raise
        publish_alert({"type": "alert"})

```
### 📄 `tests/test_rbac.py`

```python
# tests/test_rbac.py
"""Test RBAC and tenant isolation across all route modules."""
import pytest
from unittest.mock import patch, MagicMock


class TestUnauthenticatedAccess:
    """All endpoints must reject requests without auth headers."""

    PROTECTED_ROUTES = [
        ("GET", "/alerts/"),
        ("GET", "/metrics/"),
        ("GET", "/rules/"),
        ("GET", "/dimensions/"),
        ("GET", "/ml/configs/"),
        ("GET", "/incidents/"),
        ("GET", "/data/"),
        ("GET", "/data/prometheus/api/v1/label/__name__/values"),
        ("GET", "/audit/logs"),
    ]

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
    def test_no_auth_returns_401(self, api_client, method, path):
        resp = api_client.request(method, path)
        assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}"


class TestViewerPermissions:
    """Viewer users should only have read access."""

    @patch("api.routes.alerts.get_engine")
    def test_viewer_can_read_alerts(self, mock_engine, api_client, viewer_auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/alerts/", headers=viewer_auth_headers)
        assert resp.status_code == 200

    def test_viewer_cannot_suppress_alert(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/alerts/00000000-0000-0000-0000-000000000001/suppress",
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_metric(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/metrics/",
            json={"metric_name": "test", "display_name": "Test", "is_active": True},
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_rule(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/rules/",
            json={"name": "test", "condition": {}, "labels": {}, "actions": {}},
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_write_ml_config(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/ml/configs/",
            json={
                "metric_name": "test",
                "method": "prophet",
                "params": {},
                "is_active": True,
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_incident(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/incidents/",
            json={
                "alert_message": "test",
                "metric": "test_metric",
                "region": "RU-MOW",
                "priority": "low",
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403


class TestTenantIsolation:
    """Ensure tenant_id is passed to queries from auth context."""

    @patch("api.routes.alerts.get_engine")
    def test_alert_query_includes_tenant_id(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        api_client.get("/alerts/", headers=auth_headers)

        # Verify the SQL call included tenant_id param
        call_args = conn.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("parameters", {})
        assert "tenant_id" in params or "tenant_id" in str(call_args)

```
### 📄 `tests/test_resilience.py`

```python
# tests/test_resilience.py
"""Tests for graceful degradation: Redis fallback, i-doit retry queue."""
import pytest
from unittest.mock import patch, MagicMock


class TestRedisFallback:
    def test_returns_default_on_redis_error(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=[])
        def get_cached_data():
            raise ConnectionError("Redis down")

        result = get_cached_data()
        assert result == []

    def test_returns_normal_value_when_ok(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=[])
        def get_cached_data():
            return [1, 2, 3]

        result = get_cached_data()
        assert result == [1, 2, 3]

    def test_callable_default(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=dict)
        def get_data():
            raise ConnectionError("Redis down")

        result = get_data()
        assert result == {}


class TestSafeIdoitPush:
    def test_swallows_errors(self):
        from core.resilience import safe_idoit_push

        @safe_idoit_push
        def push_data():
            raise RuntimeError("i-doit connection refused")

        with patch("celery_app.celery_app") as mock_celery:
            mock_celery.send_task = MagicMock()
            result = push_data()
            assert result is None

    def test_passes_through_on_success(self):
        from core.resilience import safe_idoit_push

        @safe_idoit_push
        def push_data():
            return "ok"

        result = push_data()
        assert result == "ok"

```
### 📄 `tests/test_rules_api.py`

```python
# tests/test_rules_api.py
"""Tests for rules API: CRUD, RBAC, audit logging."""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from core.metadata_service import RuleDTO


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_rule(rule_id=None, is_active=True):
    from datetime import datetime
    mock = MagicMock()
    mock.id = rule_id or uuid4()
    mock.name = "test_rule"
    mock.description = "Test rule description"
    mock.condition = {"expr": "cpu > 90", "for": "1m", "eval": "1m"}
    mock.labels = {"severity": "critical"}
    mock.actions = [{"type": "notify", "config": {"channel": "telegram"}}]
    mock.is_active = is_active
    mock.created_at = datetime.now()
    mock.updated_at = datetime.now()
    return mock


class TestListRules:
    def test_list_active_rules(self, api_client, auth_headers, mock_metadata_service):
        rule = _make_rule()
        mock_metadata_service.list_active_rules.return_value = [rule]

        resp = api_client.get("/rules/?active_only=true", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_rule"

    def test_viewer_can_read_rules(self, api_client, viewer_auth_headers, mock_metadata_service):
        mock_metadata_service.list_active_rules.return_value = []
        resp = api_client.get("/rules/", headers=viewer_auth_headers)
        assert resp.status_code == 200


class TestCreateRule:
    @patch("api.routes.rules.log_audit")
    def test_create_rule(self, mock_audit, api_client, auth_headers, mock_metadata_service):
        import json as _json
        from datetime import datetime
        rule_id = uuid4()
        mock_metadata_service.create_rule.return_value = rule_id
        mock_metadata_service._deserialize_json.side_effect = lambda x: _json.loads(x) if isinstance(x, str) else x

        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.first.return_value = {
            "id": rule_id,
            "name": "new_rule",
            "description": "desc",
            "condition": '{"expr": "cpu > 90", "for": "1m", "eval": "1m"}',
            "labels": '{"env": "prod"}',
            "actions": '[{"type": "notify", "config": {"channel": "telegram"}}]',
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        resp = api_client.post(
            "/rules/",
            json={
                "name": "new_rule",
                "description": "desc",
                "condition": {"expr": "cpu > 90", "for": "1m", "eval": "1m"},
                "labels": {"env": "prod"},
                "actions": [{"type": "notify", "config": {"channel": "telegram"}}],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_viewer_cannot_create_rule(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/rules/",
            json={
                "name": "test",
                "condition": {},
                "labels": {},
                "actions": {},
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteRule:
    @patch("api.routes.rules.log_audit")
    def test_delete_rule(self, mock_audit, api_client, auth_headers, mock_metadata_service):
        rule_id = uuid4()
        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        result = MagicMock()
        result.rowcount = 1
        conn.execute.return_value = result

        resp = api_client.delete(f"/rules/{rule_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_rule(self, api_client, auth_headers, mock_metadata_service):
        rule_id = uuid4()
        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        result = MagicMock()
        result.rowcount = 0
        conn.execute.return_value = result

        resp = api_client.delete(f"/rules/{rule_id}", headers=auth_headers)
        assert resp.status_code == 404

```
### 📄 `tests/test_security.py`

```python
# tests/test_security.py
import pytest
from unittest.mock import patch
from core.metadata_service import MetricDTO


def test_sql_injection_protection(api_client, auth_headers):
    """Проверка защиты от SQL injection"""
    mock_metrics = [MetricDTO(metric_name="api_latency_p99", display_name="Latency", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "api_latency_p99",
                "start": 1234567890,
                "end": 1234567900,
                "step": "1s; DROP TABLE canonical_metrics; --"
            },
            headers=auth_headers,
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "step" in detail.lower()


def test_rate_limiting(api_client):
    """Проверка rate limiting"""
    rate_limit_hit = False

    for i in range(20):
        response = api_client.post("/token", data={"username": "test", "password": "test"})
        if response.status_code == 429:
            rate_limit_hit = True
            break

    assert rate_limit_hit, "Rate limiting should have been triggered"


def test_metric_whitelist(api_client, auth_headers):
    """Проверка whitelist метрик"""
    mock_metrics = [MetricDTO(metric_name="cpu_usage", display_name="CPU", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "malicious_metric",
                "start": 1234567890,
                "end": 1234567900,
                "step": "1m"
            },
            headers=auth_headers,
        )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_sql_injection_dimensions(api_client, auth_headers):
    """Тест защиты от SQL injection в dimensions"""
    mock_metrics = [MetricDTO(metric_name="api_latency_p99", display_name="Latency", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": 'api_latency_p99{region="x";DROP TABLE--"}',
                "start": 1234567890,
                "end": 1234567900,
                "step": "1m"
            },
            headers=auth_headers,
        )
    # Should be 400 Bad Request, not 500 or 200
    assert response.status_code == 400


def test_secret_masking_in_logs():
    """Убедимся, что секреты не попадают в логи"""
    from config import mask_secrets
    result = mask_secrets("redis://:super_secret_pass@localhost:6379")
    assert "super_secret_pass" not in result
    assert "***" in result

```
### 📄 `tests/load/__init__.py`

```python

```
### 📄 `tests/load/locustfile.py`

```python
# tests/load/locustfile.py
"""
Load testing with Locust.

Run:
    locust -f tests/load/locustfile.py --host http://localhost:8000

Web UI: http://localhost:8089
Headless: locust -f tests/load/locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10 -t 5m --headless
"""
import json
from locust import HttpUser, task, between, tag


class AuthMixin:
    """Get auth token once per user lifecycle."""

    _token: str = ""

    def get_headers(self):
        if not self._token:
            resp = self.client.post("/token", data={
                "username": "admin",
                "password": "admin",  # Use test password
            })
            if resp.status_code == 200:
                self._token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {self._token}"}


class ViewerUser(HttpUser, AuthMixin):
    """Simulates a viewer: reads metrics, alerts, incidents."""
    weight = 7  # 70% of traffic
    wait_time = between(1, 5)

    def on_start(self):
        self.get_headers()

    @tag("read")
    @task(5)
    def list_metrics(self):
        self.client.get("/api/v1/metrics/", headers=self.get_headers())

    @tag("read")
    @task(5)
    def list_alerts(self):
        self.client.get("/api/v1/alerts/?limit=50", headers=self.get_headers())

    @tag("read")
    @task(3)
    def list_incidents(self):
        self.client.get("/api/v1/incidents/?limit=20", headers=self.get_headers())

    @tag("read")
    @task(2)
    def list_rules(self):
        self.client.get("/api/v1/rules/", headers=self.get_headers())

    @tag("read")
    @task(1)
    def health_check(self):
        self.client.get("/health")

    @tag("read")
    @task(1)
    def list_dimensions(self):
        self.client.get("/api/v1/dimensions/", headers=self.get_headers())


class OperatorUser(HttpUser, AuthMixin):
    """Simulates an operator: reads + mutates incidents."""
    weight = 2  # 20% of traffic
    wait_time = between(2, 8)

    def on_start(self):
        self.get_headers()

    @tag("read")
    @task(4)
    def list_incidents(self):
        self.client.get("/api/v1/incidents/", headers=self.get_headers())

    @tag("read")
    @task(3)
    def list_alerts(self):
        self.client.get("/api/v1/alerts/", headers=self.get_headers())

    @tag("write")
    @task(1)
    def create_incident(self):
        self.client.post(
            "/api/v1/incidents/",
            json={
                "alert_message": "Load test incident",
                "metric": "cpu_usage",
                "region": "RU-MOW",
                "priority": "low",
                "description": "Generated by locust load test",
            },
            headers=self.get_headers(),
        )

    @tag("read")
    @task(2)
    def list_sla_policies(self):
        self.client.get("/api/v1/incidents/sla/policies", headers=self.get_headers())


class AdminUser(HttpUser, AuthMixin):
    """Simulates an admin: heavy management operations."""
    weight = 1  # 10% of traffic
    wait_time = between(5, 15)

    def on_start(self):
        self.get_headers()

    @tag("admin")
    @task(3)
    def list_users(self):
        self.client.get("/api/v1/admin/users", headers=self.get_headers())

    @tag("admin")
    @task(2)
    def list_tenants(self):
        self.client.get("/api/v1/admin/tenants", headers=self.get_headers())

    @tag("admin")
    @task(1)
    def list_audit_logs(self):
        self.client.get("/api/v1/audit/logs?limit=50", headers=self.get_headers())

    @tag("read")
    @task(2)
    def list_ml_configs(self):
        self.client.get("/api/v1/ml/configs/", headers=self.get_headers())

```
### 📄 `tests/integration/__init__.py`

```python

```
### 📄 `tests/integration/conftest.py`

```python
# tests/integration/conftest.py
"""
Integration test fixtures — connect to real PostgreSQL + Redis.

Start test infrastructure:
    docker compose -f docker-compose.test.yml up -d
Run integration tests:
    pytest tests/integration/ -v --tb=short
"""
import os
import pytest
import time

# Set env vars BEFORE importing application modules
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_pass")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5444")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6399")
os.environ.setdefault("REDIS_PASSWORD", "")
os.environ.setdefault("SECRET_KEY", "integration-test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "$2b$12$LJ3m4ys5qOzXkVzKlGT..ea.J7GIIO0C.jPBsCijMOZqMPfTpF8a6")
os.environ.setdefault("I_DOIT_API_KEY", "test")
os.environ.setdefault("I_DOIT_API_URL", "http://localhost/api")
os.environ.setdefault("WEBHOOK_API_KEY", "test-key")
os.environ.setdefault("KAFKA_ENABLED", "false")
os.environ.setdefault("CLICKHOUSE_ENABLED", "false")
os.environ.setdefault("LDAP_ENABLED", "false")
os.environ.setdefault("OIDC_ENABLED", "false")


def _wait_for_pg(max_wait=30):
    """Block until PostgreSQL is ready."""
    import psycopg2
    start = time.time()
    while time.time() - start < max_wait:
        try:
            conn = psycopg2.connect(
                host="localhost", port=5444,
                user="test_user", password="test_pass", dbname="test_db",
            )
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    pytest.skip("PostgreSQL not available at localhost:5444 — run docker compose -f docker-compose.test.yml up -d")


def _wait_for_redis(max_wait=15):
    """Block until Redis is ready."""
    import redis as r
    start = time.time()
    while time.time() - start < max_wait:
        try:
            client = r.Redis(host="localhost", port=6399)
            client.ping()
            client.close()
            return True
        except Exception:
            time.sleep(0.5)
    pytest.skip("Redis not available at localhost:6399 — run docker compose -f docker-compose.test.yml up -d")


@pytest.fixture(scope="session", autouse=True)
def _wait_for_infra():
    _wait_for_pg()
    _wait_for_redis()


@pytest.fixture(scope="session")
def db_engine():
    from sqlalchemy import create_engine
    engine = create_engine("postgresql://test_user:test_pass@localhost:5444/test_db")
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def real_redis():
    import redis as r
    client = r.Redis(host="localhost", port=6399, decode_responses=True)
    yield client
    client.flushdb()
    client.close()


@pytest.fixture(scope="session")
def integration_client():
    """FastAPI TestClient connected to real test DB."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(integration_client):
    """Get a real admin JWT token."""
    resp = integration_client.post("/token", data={
        "username": "admin",
        "password": "admin",
    })
    if resp.status_code != 200:
        pytest.skip(f"Cannot get admin token: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

```
### 📄 `tests/integration/test_end_to_end.py`

```python
# tests/integration/test_end_to_end.py
"""
End-to-end integration tests with real PostgreSQL and Redis.

Prerequisites:
    docker compose -f docker-compose.test.yml up -d
    pytest tests/integration/ -v
"""
import pytest
from sqlalchemy import text


class TestHealthAndAuth:
    def test_health_endpoint(self, integration_client):
        resp = integration_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_login_env_admin(self, integration_client):
        resp = integration_client.post("/token", data={
            "username": "admin",
            "password": "admin",
        })
        # May return 200 or 401 depending on whether bcrypt hash matches "admin"
        assert resp.status_code in (200, 401)

    def test_unauthenticated_rejected(self, integration_client):
        resp = integration_client.get("/api/v1/metrics/")
        assert resp.status_code in (401, 403)


class TestMetricsCRUD:
    def test_create_and_list_metrics(self, integration_client, admin_headers, db_engine):
        # Ensure table exists
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM metadata_metrics LIMIT 1"))
        except Exception:
            pytest.skip("metadata_metrics table not found — migrations not applied")

        # Create metric
        resp = integration_client.post(
            "/api/v1/metrics/",
            json={
                "metric_name": "inttest_cpu_usage",
                "display_name": "CPU Usage (integration test)",
                "unit": "percent",
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert resp.status_code in (201, 400)  # 400 if already exists

        # List metrics
        resp = integration_client.get("/api/v1/metrics/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_metric(self, integration_client, admin_headers):
        resp = integration_client.get("/api/v1/metrics/inttest_cpu_usage", headers=admin_headers)
        assert resp.status_code in (200, 404)


class TestIncidentLifecycle:
    def test_full_lifecycle(self, integration_client, admin_headers, db_engine):
        # Check table exists
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM incidents LIMIT 1"))
        except Exception:
            pytest.skip("incidents table not found — migrations not applied")

        # Create incident
        resp = integration_client.post(
            "/api/v1/incidents/",
            json={
                "alert_message": "Integration test incident",
                "metric": "cpu_usage",
                "region": "RU-MOW",
                "priority": "low",
            },
            headers=admin_headers,
        )
        if resp.status_code != 201:
            pytest.skip(f"Create incident failed: {resp.status_code}")

        incident_id = resp.json()["id"]

        # Transition: new -> in_progress
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "in_progress"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

        # Assign
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/assign",
            json={"assigned_to": "test-operator"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # Add comment
        resp = integration_client.post(
            f"/api/v1/incidents/{incident_id}/comments",
            json={"content": "Investigation started by integration test"},
            headers=admin_headers,
        )
        assert resp.status_code == 201

        # List comments
        resp = integration_client.get(
            f"/api/v1/incidents/{incident_id}/comments",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Resolve
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "resolved", "comment": "Fixed by integration test"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # Close
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "closed"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_invalid_transition(self, integration_client, admin_headers, db_engine):
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM incidents LIMIT 1"))
        except Exception:
            pytest.skip("incidents table not found")

        resp = integration_client.post(
            "/api/v1/incidents/",
            json={
                "alert_message": "Transition test",
                "metric": "mem_usage",
                "region": "RU-SPE",
                "priority": "medium",
            },
            headers=admin_headers,
        )
        if resp.status_code != 201:
            pytest.skip(f"Create incident failed: {resp.status_code}")

        incident_id = resp.json()["id"]

        # Invalid: new -> resolved (must go through in_progress)
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "resolved"},
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestTenantIsolation:
    def test_data_scoped_to_tenant(self, integration_client, admin_headers, db_engine):
        """Verify that list endpoints return tenant-scoped data."""
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM metadata_metrics LIMIT 1"))
        except Exception:
            pytest.skip("metadata_metrics table not found")

        resp = integration_client.get("/api/v1/metrics/", headers=admin_headers)
        assert resp.status_code == 200
        # All returned metrics should belong to the admin's tenant (default)
        # We can't assert tenant_id directly since it's not in MetricRead,
        # but we verify the query doesn't error out with tenant filtering


class TestApiVersioning:
    def test_v1_route_no_deprecation(self, integration_client, admin_headers):
        resp = integration_client.get("/api/v1/metrics/", headers=admin_headers)
        assert "Deprecation" not in resp.headers

    def test_legacy_route_has_deprecation(self, integration_client, admin_headers):
        resp = integration_client.get("/metrics/", headers=admin_headers)
        if resp.status_code == 200:
            assert resp.headers.get("Deprecation") == "true"
            assert "Sunset" in resp.headers


class TestAlertEndpoints:
    def test_list_alerts(self, integration_client, admin_headers, db_engine):
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM alert_events LIMIT 1"))
        except Exception:
            pytest.skip("alert_events table not found")

        resp = integration_client.get("/api/v1/alerts/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

```
### 📄 `grafana/provisioning/datasources/postgres.yaml`

```yaml
apiVersion: 1
datasources:
  - name: PostgreSQL
    type: postgres
    access: proxy
    url: db:5432
    database: monitoring_db
    user: ${POSTGRES_USER}
    secureJsonData:
      password: "${POSTGRES_PASSWORD}"
    jsonData:
      sslmode: "disable"
      maxOpenConns: 10
      maxIdleConns: 10
      connMaxLifetime: 14400
    isDefault: true
```
### 📄 `grafana/provisioning/dashboards/dashboard.yml`

```yaml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
```
### 📄 `core/__init__.py`

```python

```
### 📄 `core/alert_settings.py`

```python
# core/alert_settings.py
from typing import Dict
from dataclasses import dataclass, asdict, field
import json
from config import get_cache, logger
from core.metric_service import load_metrics_from_db_cached
import time
import threading

ALERT_SETTINGS_KEY = "alert_settings"
_alert_settings_cache = None
_last_cache_update = 0
_cache_lock = threading.Lock()

@dataclass
class AlertSettings:
    # Пороги по метрикам (display_name -> threshold)
    thresholds: Dict[str, int] = field(default_factory=dict)
    # Умные алерты: рост
    smart_growth_enabled: bool = True
    smart_growth: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Умные алерты: отклонение
    smart_deviation_enabled: bool = True
    smart_deviation: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Включены ли вообще уведомления

    alerts_enabled: bool = True

    priority_multipliers: Dict[str, float] = field(default_factory=dict)

    # 🔥 НОВОЕ: подавление алертов
    suppression_enabled: bool = True
    suppression_minutes: Dict[str, int] = field(default_factory=lambda: {
        "complaints": 60,   # 1 час для жалоб
        "closed": 30,       # 30 мин для сети
        "delays": 45,       # 45 мин для задержек
    })
    # По умолчанию — 30 минут для всех метрик, если не указано
    default_suppression_minutes: int = 30

    escalation_enabled: bool = True
    escalation_growth_threshold: float = 25.0  # Минимальный процент роста для эскалации
    escalation_critical_threshold: float = 50.0  # Порог для критической эскалации

    def get_suppression_seconds(self, metric_display_name: str) -> int:
        """Возвращает время подавления в секундах для метрики."""
        minutes = self.suppression_minutes.get(
            metric_display_name,
            self.default_suppression_minutes
        )
        return max(minutes, 5) * 60  # минимум 5 минут

    def get_suppression_minutes(self, metric_display_name: str) -> int:
        """Возвращает время подавления в минутах для метрики."""
        return self.suppression_minutes.get(
            metric_display_name,
            self.default_suppression_minutes
        )

    def __post_init__(self):
        """
        Заполняет дефолтные значения из БД, если настройки пусты.
        Используется при первом запуске или повреждённых данных в Redis.
        """
        # Загружаем метрики из БД
        metrics = load_metrics_from_db_cached()

        # 1. Дефолтные пороги: display_name -> threshold
        if not self.thresholds:
            self.thresholds = {m.display_name: m.threshold for m in metrics}
            logger.info("✅ Пороги алертов инициализированы из БД (по умолчанию)")

        # 2. Smart Growth (рост)
        if not self.smart_growth:
            default_growth = {
                "complaints": {"percent": 50, "period_minutes": 60},
                "closed": {"percent": 100, "period_minutes": 30},
            }
            # Оставляем только те, что есть в метриках
            self.smart_growth = { # type: ignore
                m.column: default_growth[m.column]
                for m in metrics
                if m.column in default_growth
            }
            logger.info(f"✅ Smart Growth инициализирован для: {list(self.smart_growth.keys())}")

        # 3. Smart Deviation (отклонение)
        if not self.smart_deviation:
            default_deviation = {
                "closed": {"std_dev": 2.0},
                "delays": {"std_dev": 1.5},
            }
            self.smart_deviation = {
                m.column: default_deviation[m.column]
                for m in metrics
                if m.column in default_deviation
            }
            logger.info(f"✅ Smart Deviation инициализирован для: {list(self.smart_deviation.keys())}")
            
        if not self.priority_multipliers:
            self.priority_multipliers = {
                "warning": 1.0,
                "critical": 1.5
            }
        # 4. Настройки эскалации по умолчанию
        if not hasattr(self, 'escalation_enabled'):
            self.escalation_enabled = True
        if not hasattr(self, 'escalation_growth_threshold'):
            self.escalation_growth_threshold = 25.0
        if not hasattr(self, 'escalation_critical_threshold'):
            self.escalation_critical_threshold = 50.0


def load_alert_settings_cached(force_refresh=False):
    global _alert_settings_cache, _last_cache_update
    
    # Быстрая проверка без блокировки
    if not force_refresh and _alert_settings_cache and time.time() - _last_cache_update < 300:
        return _alert_settings_cache
    
    with _cache_lock:
        # Double-check после получения блокировки
        if not force_refresh and _alert_settings_cache and time.time() - _last_cache_update < 300:
            return _alert_settings_cache
        
        settings = load_alert_settings()
        _alert_settings_cache = settings
        _last_cache_update = time.time()
        return settings

def load_alert_settings() -> AlertSettings:
    # 1. Загружаем базовые пороги из БД
    metrics = load_metrics_from_db_cached()
    default_thresholds = {m.display_name: m.threshold for m in metrics}

    # 2. Читаем кастомные настройки из Redis
    try:
        data = get_cache().get(ALERT_SETTINGS_KEY)
        if data:
            loaded = json.loads(data) # type: ignore
            settings = AlertSettings(**loaded)
            # Заполняем пропущенные пороги из БД
            for metric in metrics:
                if metric.display_name not in settings.thresholds:
                    settings.thresholds[metric.display_name] = metric.threshold
            return settings
    except Exception as e:
        logger.warning(f"Не удалось загрузить настройки алертов: {e}")

    # 3. Дефолт: базовые пороги + глобальные настройки
    return AlertSettings(
        thresholds=default_thresholds,
        smart_growth_enabled=True,
        smart_deviation_enabled=True
    )

def save_alert_settings(settings: AlertSettings):
    try:
        data = json.dumps(asdict(settings))
        get_cache().setex(ALERT_SETTINGS_KEY, 86400 * 7, data)  # 7 дней
        logger.info("Настройки алертов сохранены в Redis")
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек алертов: {e}")
    

```
### 📄 `core/alerts.py`

```python
# core/alerts.py
import time
import hashlib
from datetime import datetime, timedelta, timezone
import threading
from queue import Queue, Empty
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass
import pandas as pd
from config import settings, logger, get_cache, get_database_url
from core.database import get_engine
from core.notifications import notify
from core.smart_alerts import check_growth_alert, check_deviation_alert
from core.alert_settings import AlertSettings, load_alert_settings_cached
from core.metric_service import get_metric_by_column
from core.models import AlertEvent, Incident
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import json

incident_queue = Queue(maxsize=100)
buffer_event = threading.Event()
_incident_processor_started = False
_last_check_times = {}

@dataclass
class AlertLog:
    timestamp: float
    metric: str
    region: str
    value: float
    priority: str = "info"

def get_engine_proxy():
    return get_engine()

def generate_alert_hash(metric: str, region: str, value: float) -> str:
    return hashlib.md5(f"{metric}_{region}_{value}".encode()).hexdigest()

def is_alert_suppressed(alert_hash: str, tenant_id: str = "default") -> bool:
    """Проверяет, подавлен ли алерт."""
    try:
        return get_cache().get(f"alert_suppression:{tenant_id}:{alert_hash}") is not None
    except Exception:
        return False


def are_alerts_suppressed(alert_hashes: list, tenant_id: str = "default") -> dict:
    """Пакетная проверка подавления алертов."""
    if not alert_hashes:
        return {}

    cache = get_cache()
    keys = [f"alert_suppression:{tenant_id}:{h}" for h in alert_hashes]

    try:
        pipe = cache.pipeline()
        for key in keys:
            pipe.exists(key)
        results = pipe.execute()

        return {h: bool(r) for h, r in zip(alert_hashes, results)}
    except Exception:
        return {h: False for h in alert_hashes}

def suppress_alert(alert_hash: str, minutes: int, tenant_id: str = "default"):
    if alert_hash.startswith("escalation_"):
        return
    get_cache().setex(f"alert_suppression:{tenant_id}:{alert_hash}", minutes * 60, "1")

def track_escalation_data(metric: str, region: str, value: float, tenant_id: str = "default"):
    cache = get_cache()
    key = f"escalation_tracker:{tenant_id}:{metric}:{region}"
    hist = cache.get(key)
    hist = json.loads(hist) if hist else []
    hist.append({"timestamp": time.time(), "value": value})
    hist = hist[-10:]
    cache.setex(key, 3600, json.dumps(hist))

def is_steady_increase(vals: List[float]) -> bool:
    return len(vals) >= 3 and all(vals[i] > vals[i-1] for i in range(1, len(vals)))

def check_escalation_alert(metric: str, region: str, current_value: float, is_suppressed: bool, tenant_id: str = "default") -> Optional[Tuple[str, str]]:
    if not is_suppressed:
        return None
    cache = get_cache()
    key = f"escalation_tracker:{tenant_id}:{metric}:{region}"
    hist_raw = cache.get(key)
    if not hist_raw:
        return None
    try:
        hist = json.loads(hist_raw)
        if len(hist) < 3:
            return None
        vals = [h["value"] for h in hist]
        if is_steady_increase(vals):
            growth = ((current_value - vals[0]) / vals[0]) * 100 if vals[0] > 0 else 100
            if growth > 50:
                return (f"🚨 ЭСКАЛАЦИЯ: {metric} в {region} вырос на {growth:.1f}% до {current_value}!", "critical")
            elif growth > 25:
                return (f"⚠️ Эскалация: {metric} в {region} вырос на {growth:.1f}%", "warning")
    except Exception as e:
        logger.warning(f"Ошибка эскалации: {e}")
    return None

def create_incident_buffered(alert_message: str, metric: str, region: str, value: float, priority: str, tenant_id: str = "default"):
    data = {
        "alert_message": alert_message,
        "metric": metric,
        "region": region,
        "value": str(value),
        "priority": priority,
        "tenant_id": tenant_id,
        "detected_at": datetime.now(timezone.utc),
    }
    try:
        incident_queue.put(data, timeout=1)
        if incident_queue.qsize() >= 80:
            buffer_event.set()
    except Exception as e:
        logger.error(f"Очередь переполнена: {e}")
        _create_incident_directly(data)

def _create_incident_directly(data: Dict):
    engine = get_engine_proxy()
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        incident = Incident(**data)
        s.add(incident)
        s.commit()
        # Apply SLA policy
        try:
            from core.sla_service import apply_sla_to_incident
            apply_sla_to_incident(
                incident.id,
                data.get("tenant_id", "default"),
                data.get("priority", "medium"),
                data.get("detected_at", datetime.now(timezone.utc)),
            )
        except Exception as e:
            logger.warning(f"Failed to apply SLA to auto-created incident: {e}")
        # Push to i-doit
        try:
            from core.idoit_service import push_incident_create
            push_incident_create(incident.id)
        except Exception as e:
            logger.warning(f"Failed to push auto-created incident to i-doit: {e}")
    except Exception as e:
        s.rollback()
        logger.error(f"❌ Прямое создание инцидента упало: {e}")
    finally:
        s.close()

def process_incident_buffer():
    logger.info("🔄 Запущен процессор инцидентов")
    while True:
        try:
            buffer_event.wait(timeout=30)
            buffer_event.clear()
            batch = []
            while not incident_queue.empty() and len(batch) < 20:
                try:
                    batch.append(incident_queue.get_nowait())
                except Empty:
                    break
            if not batch:
                continue

            engine = get_engine_proxy()
            Session = sessionmaker(bind=engine)
            s = Session()
            try:
                s.bulk_insert_mappings(Incident, batch)
                s.commit()
                logger.info(f"✅ Пакет инцидентов: {len(batch)}")
            except Exception as e:
                s.rollback()
                logger.error(f"❌ Ошибка пакета: {e}")
                for item in batch:
                    incident_queue.put_nowait(item)
            finally:
                s.close()
        except Exception as e:
            logger.exception(f"💥 Критическая ошибка в процессоре: {e}")
            time.sleep(5)

def start_incident_buffer_processor():
    global _incident_processor_started
    if _incident_processor_started:
        return
    _incident_processor_started = True
    t = threading.Thread(target=process_incident_buffer, daemon=True, name="IncidentProcessor")
    t.start()
    logger.info("✅ Процессор инцидентов запущен")

def get_alert_history(tenant_id: str = "default") -> List[AlertLog]:
    try:
        raw = get_cache().get(f"alert_history:{tenant_id}")
        if raw:
            return [AlertLog(**item) for item in json.loads(raw)]
    except Exception as e:
        logger.warning(f"Ошибка чтения истории: {e}")
    return []

def save_alert_history(history: List[AlertLog], tenant_id: str = "default"):
    if len(history) > 100:
        history = history[-100:]
    try:
        data = [a.__dict__ for a in history]
        get_cache().setex(f"alert_history:{tenant_id}", 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")

def check_for_alerts(df: pd.DataFrame, col: str, selected: str, last_alert_region: str, alert_settings: AlertSettings, tenant_id: str = "default") -> Tuple[bool, str]:
    now = time.time()
    if col in _last_check_times and now - _last_check_times[col] < 30:
        return False, last_alert_region
    _last_check_times[col] = now

    if df.empty or col not in df.columns:
        return False, last_alert_region

    if not alert_settings.alerts_enabled:
        return False, last_alert_region

    metric = get_metric_by_column(col)
    if not metric:
        return False, last_alert_region

    max_idx = df[col].idxmax()
    region = str(df.iloc[max_idx].get("region", "N/A"))
    val = df.iloc[max_idx].get(col, 0)
    if hasattr(val, "item"):
        val = val.item()
    if not pd.notna(val):
        return False, last_alert_region

    alert_hash = generate_alert_hash(col, region, val)
    is_suppressed = is_alert_suppressed(alert_hash, tenant_id=tenant_id)

    escalation = check_escalation_alert(col, region, val, is_suppressed, tenant_id=tenant_id)
    if escalation:
        msg, prio = escalation
        notify(msg, prio)
        create_incident_buffered(msg, col, region, val, prio, tenant_id=tenant_id)
        track_escalation_data(col, region, val, tenant_id=tenant_id)
        return True, region

    if is_suppressed:
        return False, last_alert_region

    # Основные проверки
    msg = None
    prio = "info"

    if alert_settings.smart_growth_enabled:
        msg = check_growth_alert(df, col, selected, alert_settings)
        if msg:
            prio = "critical"

    if not msg and alert_settings.smart_deviation_enabled:
        msg = check_deviation_alert(df, col, selected, alert_settings)
        if msg:
            prio = "warning"

    if not msg and val > alert_settings.thresholds.get(selected, metric.threshold):
        msg = f"🚨 {selected}: {region} — {int(val)}"
        crit_mult = alert_settings.priority_multipliers.get("critical", 1.5)
        prio = "critical" if val > alert_settings.thresholds.get(selected, metric.threshold) * crit_mult else "warning"

    if not msg:
        try:
            from core.ml_anomaly import find_recent_ml_anomalies
            anomalies = find_recent_ml_anomalies(
                time_filter="1h",
                metrics=[col]
            )
            recent = [
                a for a in anomalies
                if a["metric_name"] == col and a["dimensions"].get("region") == region
                and pd.Timestamp(a["timestamp"]) > pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
            ]
            if recent:
                latest = recent[0]
                msg = f"🤖 ML: {region} — {latest['value']:.1f} (прогноз: {latest['predicted']:.1f})"
                prio = "critical"
        except Exception as e:
            logger.warning(f"ML проверка упала: {e}")

    if not msg:
        return False, last_alert_region

    # Сохранение алерта
    engine = get_engine_proxy()
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        existing = s.query(AlertEvent).filter_by(alert_hash=alert_hash, tenant_id=tenant_id).first()
        if existing and existing.sent_at and (
            datetime.now(timezone.utc) - existing.sent_at < timedelta(minutes=alert_settings.get_suppression_minutes(selected))
        ):
            suppress_alert(alert_hash, alert_settings.get_suppression_minutes(selected), tenant_id=tenant_id)
            return False, last_alert_region

        new_alert = AlertEvent(
            alert_hash=alert_hash,
            metric_name=selected,
            dimensions={"region": region},
            value=val,
            event_time=datetime.now(timezone.utc),
            detected_at=datetime.now(timezone.utc),
            status="firing",
            sent=False,
            fingerprint=alert_hash,
            tenant_id=tenant_id,
        )
        s.add(new_alert)
        s.flush()

        # Отправка
        notify(msg, prio)
        new_alert.sent = True
        new_alert.sent_at = datetime.now(timezone.utc)

        # Инцидент
        create_incident_buffered(msg, selected, region, val, prio, tenant_id=tenant_id)
        new_alert.incident_created = True
        new_alert.incident_created_at = datetime.now(timezone.utc)

        s.commit()

        # Publish to Redis Pub/Sub for WebSocket clients
        alert_payload = {
            "type": "alert",
            "id": str(new_alert.id),
            "metric": selected,
            "dimensions": {"region": region},
            "value": float(val),
            "status": "firing",
            "event_time": new_alert.event_time.isoformat(),
        }
        try:
            from core.pubsub import publish_alert
            publish_alert(alert_payload)
        except Exception as e:
            logger.warning(f"Failed to publish alert to pubsub: {e}")

        # Publish to Kafka if enabled
        try:
            if settings.KAFKA_ENABLED:
                from core.kafka_producer import publish_alert_event
                publish_alert_event(alert_payload)
        except Exception as e:
            logger.warning(f"Failed to publish alert to Kafka: {e}")

        # История
        history = get_alert_history(tenant_id=tenant_id)
        history.append(AlertLog(time.time(), selected, region, val, prio))
        save_alert_history(history, tenant_id=tenant_id)

        logger.info(f"✅ Алерт создан: {new_alert.id}")
        return True, region

    except IntegrityError:
        s.rollback()
        return False, last_alert_region
    except Exception as e:
        s.rollback()
        logger.exception(f"❌ Ошибка алерта: {e}")
        return False, last_alert_region
    finally:
        s.close()

```
### 📄 `core/analytics_service.py`

```python
# core/analytics_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import logger, mask_secrets


class AnalyticsService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from core.clickhouse import get_clickhouse_client
            self._client = get_clickhouse_client()
        return self._client

    def query_metric_aggregation(
        self,
        metric_name: str,
        start: datetime,
        end: datetime,
        aggregation: str = "avg",
        interval: str = "1 HOUR",
        tenant_id: str = "default",
        dimension_filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        allowed_aggs = {"avg", "sum", "min", "max", "count"}
        if aggregation not in allowed_aggs:
            aggregation = "avg"

        query = f"""
            SELECT
                toStartOfInterval(timestamp, INTERVAL {interval}) AS bucket,
                {aggregation}(value) AS agg_value,
                count() AS sample_count
            FROM sit_center.metrics
            WHERE metric_name = {{metric_name:String}}
              AND timestamp >= {{start:DateTime64(3)}}
              AND timestamp <= {{end:DateTime64(3)}}
              AND tenant_id = {{tenant_id:String}}
            GROUP BY bucket
            ORDER BY bucket
        """
        params = {
            "metric_name": metric_name,
            "start": start,
            "end": end,
            "tenant_id": tenant_id,
        }

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"bucket": str(row[0]), "value": row[1], "count": row[2]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_metric_aggregation failed: %s", mask_secrets(str(e)))
            return []

    def query_top_n_metrics(
        self,
        start: datetime,
        end: datetime,
        n: int = 10,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                metric_name,
                count() AS cnt,
                avg(value) AS avg_value,
                max(value) AS max_value
            FROM sit_center.metrics
            WHERE timestamp >= {start:DateTime64(3)}
              AND timestamp <= {end:DateTime64(3)}
              AND tenant_id = {tenant_id:String}
            GROUP BY metric_name
            ORDER BY cnt DESC
            LIMIT {n:UInt32}
        """
        params = {"start": start, "end": end, "tenant_id": tenant_id, "n": n}

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"metric_name": row[0], "count": row[1], "avg_value": row[2], "max_value": row[3]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_top_n_metrics failed: %s", mask_secrets(str(e)))
            return []

    def query_alert_statistics(
        self,
        start: datetime,
        end: datetime,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                metric_name,
                status,
                count() AS cnt
            FROM sit_center.alerts
            WHERE event_time >= {start:DateTime64(3)}
              AND event_time <= {end:DateTime64(3)}
              AND tenant_id = {tenant_id:String}
            GROUP BY metric_name, status
            ORDER BY cnt DESC
        """
        params = {"start": start, "end": end, "tenant_id": tenant_id}

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"metric_name": row[0], "status": row[1], "count": row[2]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_alert_statistics failed: %s", mask_secrets(str(e)))
            return []


analytics_service = AnalyticsService()

```
### 📄 `core/audit.py`

```python
# core/audit.py
import json
from typing import Optional, Dict, Any
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine


def log_audit(
    username: str,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write an audit log entry to the database."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO audit_log (username, tenant_id, action, resource_type, resource_id, changes, ip_address, user_agent)
                    VALUES (:username, :tenant_id, :action, :resource_type, :resource_id, :changes, :ip_address, :user_agent)
                """),
                {
                    "username": username,
                    "tenant_id": tenant_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "changes": json.dumps(changes or {}, ensure_ascii=False, default=str),
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                },
            )
    except Exception as e:
        logger.error("Failed to write audit log: %s", mask_secrets(str(e)))

```
### 📄 `core/auth_strategies.py`

```python
# core/auth_strategies.py
"""Authentication strategies: LDAP, DB-based, env-based admin fallback."""
import json
from datetime import timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import text as sa_text

from api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from config import logger, settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _make_token(sub: str, tenant_id: str, roles: list, permissions: list) -> str:
    return create_access_token(
        data={
            "sub": sub,
            "scopes": ["admin"] if "admin" in roles else [],
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": list(set(permissions)),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def try_ldap_auth(username: str, password: str) -> Optional[str]:
    """Try LDAP authentication. Returns access_token or None."""
    if not getattr(settings, "LDAP_ENABLED", False):
        return None
    try:
        from core.ldap_auth import ldap_authenticator
        ldap_user = ldap_authenticator.authenticate(username, password)
        if not ldap_user:
            return None
        ldap_authenticator.sync_user_to_db(ldap_user)
        roles = ldap_authenticator.get_roles_for_groups(ldap_user.groups)
        all_perms: list = []
        from core.database import get_engine
        engine = get_engine()
        for role_name in roles:
            with engine.connect() as c:
                r = c.execute(
                    sa_text("SELECT permissions FROM roles WHERE name = :name AND tenant_id = 'default'"),
                    {"name": role_name},
                ).mappings().first()
                if r:
                    perms = r["permissions"]
                    all_perms.extend(json.loads(perms) if isinstance(perms, str) else perms)
        return _make_token(ldap_user.username, "default", roles, all_perms)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"LDAP auth failed, falling back: {e}")
        return None


def try_db_auth(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Try DB-based user authentication. Returns {token, username, tenant_id} or None."""
    try:
        from core.database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            user_row = conn.execute(
                sa_text("""
                    SELECT u.id, u.username, u.password_hash, u.tenant_id, u.is_active,
                           COALESCE(
                               json_agg(DISTINCT r.name) FILTER (WHERE r.name IS NOT NULL),
                               '[]'
                           ) AS roles,
                           COALESCE(
                               json_agg(DISTINCT perm) FILTER (WHERE perm IS NOT NULL),
                               '[]'
                           ) AS permissions
                    FROM users u
                    LEFT JOIN user_roles ur ON u.id = ur.user_id
                    LEFT JOIN roles r ON ur.role_id = r.id
                    LEFT JOIN LATERAL jsonb_array_elements_text(r.permissions) AS perm ON true
                    WHERE u.username = :username AND u.is_active = true
                    GROUP BY u.id, u.username, u.password_hash, u.tenant_id, u.is_active
                """),
                {"username": username},
            ).mappings().first()

            if not user_row or not user_row["password_hash"]:
                return None
            if not pwd_context.verify(password, user_row["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            token = _make_token(
                user_row["username"],
                user_row["tenant_id"],
                user_row["roles"] or [],
                user_row["permissions"] or [],
            )
            return {"token": token, "username": user_row["username"], "tenant_id": user_row["tenant_id"]}
    except HTTPException:
        raise
    except Exception:
        return None


def try_env_admin_auth(username: str, password: str) -> str:
    """Env-based admin fallback. Raises HTTPException on failure."""
    if username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _make_token(
        username,
        "default",
        ["admin"],
        [
            "read:metrics", "write:metrics", "read:rules", "write:rules",
            "read:alerts", "write:alerts", "read:ml", "write:ml",
            "admin:tenants", "admin:users", "read:audit",
        ],
    )

```
### 📄 `core/celery_metrics.py`

```python
# core/celery_metrics.py
import time
from prometheus_client import Histogram, Counter
from celery.signals import task_prerun, task_postrun, task_failure

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution duration in seconds",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

celery_task_failures_total = Counter(
    "celery_task_failures_total",
    "Total Celery task failures",
    ["task_name"],
)

_task_start_times = {}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, **kwargs):
    _task_start_times[task_id] = time.perf_counter()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, **kwargs):
    start = _task_start_times.pop(task_id, None)
    if start is not None:
        duration = time.perf_counter() - start
        task_name = getattr(sender, "name", "unknown")
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


@task_failure.connect
def task_failure_handler(sender=None, **kwargs):
    task_name = getattr(sender, "name", "unknown")
    celery_task_failures_total.labels(task_name=task_name).inc()

```
### 📄 `core/clickhouse.py`

```python
# core/clickhouse.py
import threading
from config import settings, logger, mask_secrets

_client = None
_lock = threading.Lock()


def get_clickhouse_client():
    global _client
    if _client is not None:
        return _client

    with _lock:
        if _client is not None:
            return _client

        import clickhouse_connect

        host = getattr(settings, "CLICKHOUSE_HOST", "clickhouse")
        port = int(getattr(settings, "CLICKHOUSE_PORT", 8123))
        user = getattr(settings, "CLICKHOUSE_USER", "default")
        password = getattr(settings, "CLICKHOUSE_PASSWORD", "")
        database = getattr(settings, "CLICKHOUSE_DB", "sit_center")

        try:
            _client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=user,
                password=password,
                database=database,
            )
            logger.info("ClickHouse client initialized (%s:%s/%s)", host, port, database)
        except Exception as e:
            logger.error("Failed to connect to ClickHouse: %s", mask_secrets(str(e)))
            raise

    return _client

```
### 📄 `core/config_service.py`

```python
# core/config_service.py
import json
from typing import Dict, List
from importlib import import_module
from sqlalchemy import select
from config import get_cache,logger, mask_secrets
from core.database import get_engine
from core.models import ConfigTable

class ConfigService:
    def __init__(self):
        self._registry: Dict[str, Dict] = {}
        self._load_registry()

    def _load_registry(self):
        """Загружает реестр таблиц из БД"""
        try:
            engine = get_engine()
            with engine.connect() as conn: # type: ignore
                result = conn.execute(select(ConfigTable))
                rows = result.fetchall()
                self._registry = {
                    row.name: {
                        "model_class": row.model_class,
                        "cache_key": row.cache_key,
                        "ttl": row.ttl,
                        "schema_name": row.schema_name,
                        "is_active": row.is_active
                    }
                    for row in rows if row.is_active
                }
            logger.info(f"✅ Реестр конфигураций загружен: {len(self._registry)} активных таблиц")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки реестра config_tables: {mask_secrets(str(e))}")
            # Fallback: использовать минимальный набор
            self._registry = {
                "metrics": {
                    "model_class": "core.models.Metric",
                    "cache_key": "config:metrics",
                    "ttl": 300
                }
            }

    def _import_model(self, model_path: str):
        try:
            module_path, class_name = model_path.rsplit(".", 1)
            module = import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"❌ Не удалось импортировать модель {model_path}: {e}")
            return None

    def _fetch_from_db(self, table_config: Dict) -> List[Dict]:
        model = self._import_model(table_config["model_class"])
        if not model:
            return []

        engine = get_engine()
        try:
            with engine.connect() as conn: # type: ignore
                result = conn.execute(select(model))
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка чтения из {model.__tablename__}: {mask_secrets(str(e))}")
            return []

    def get(self, table_name: str, force_refresh: bool = False) -> List[Dict]:
        """Получить данные конфигурации по имени таблицы"""
        if table_name not in self._registry:
            logger.warning(f"⚠️ Таблица '{table_name}' не найдена в config_tables")
            return []

        config = self._registry[table_name]
        cache = get_cache()
        cache_key = config["cache_key"]

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                try:
                    return json.loads(cached) # type: ignore
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка парсинга кэша {cache_key}: {mask_secrets(str(e))}")

        # Загружаем из БД
        data = self._fetch_from_db(config)
        if data:
            cache.setex(
                cache_key,
                config["ttl"],
                json.dumps(data, ensure_ascii=False, default=str)
            )
            logger.info(f"🔁 Кэш обновлён: {cache_key} ({len(data)} записей)")
        else:
            logger.warning(f"⚠️ Нет данных для {table_name}")

        return data

    def refresh(self, table_name: str = None): # type: ignore
        """Обновить кэш одной или всех таблиц"""
        if table_name:
            if table_name in self._registry:
                self.get(table_name, force_refresh=True)
            else:
                logger.warning(f"Таблица {table_name} не найдена")
        else:
            for name in self._registry:
                self.get(name, force_refresh=True)

    def list_tables(self) -> List[Dict]:
        """Возвращает список всех активных конфигурационных таблиц"""
        return [
            {"name": k, **v} for k, v in self._registry.items()
        ]
```
### 📄 `core/data.py`

```python
# core/data.py
import pandas as pd
from config import settings, logger, get_cache, mask_secrets
from datetime import datetime, timedelta
from sqlalchemy import text
import io
from core.database import get_engine
from core.metadata_service import metadata_service


CACHE_TTL = settings.cache_ttl

def create_mv():
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text(
                "CALL refresh_continuous_aggregate('cagg_hourly_metrics', NULL, NULL);"
            ))
            logger.info("cagg_hourly_metrics refreshed via TimescaleDB")
            return True
    except Exception as e:
        logger.warning(f"TimescaleDB cagg refresh failed, trying legacy MV: {e}")
        try:
            engine = get_engine()
            with engine.begin() as conn:
                conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY cagg_hourly_metrics;"))
                logger.info("cagg_hourly_metrics refreshed (CONCURRENTLY fallback)")
                return True
        except Exception as e2:
            logger.error(f"MV refresh failed: {e2}")
            return False

def get_data_from_db(time_filter: str = "1h", fill_missing: str = "zero") -> pd.DataFrame:
    """Загружает данные из PostgreSQL с улучшенной обработкой ошибок"""
    key = f"data_from_db_{time_filter}_{fill_missing}"

    try:
        data = get_cache().get(key)
        if data:
            df = pd.read_json(io.StringIO(data), orient="split") # type: ignore
            logger.debug(f"Данные загружены из Redis: {key}")
            return df
    except Exception as e:
        logger.warning(f"Ошибка загрузки из Redis: {mask_secrets(str(e))}")

    try:
        engine = get_engine()
        now = datetime.now()
        time_deltas = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "2d": timedelta(days=2),
            "3d": timedelta(days=3),
            "5d": timedelta(days=5),
            "10d": timedelta(days=10),
        }
        cutoff = now - time_deltas.get(time_filter, timedelta(hours=1))

        # 🔴 ИСПРАВЛЕНО: динамический SELECT по метрикам из metadata_metrics
        metrics = [m.metric_name for m in metadata_service.list_metrics(active_only=True)]
        if not metrics:
            logger.warning("⚠️ Нет активных метрик для загрузки")
            metrics = ["complaints", "closed"]  # fallback

        case_expressions = [
            f"MAX(CASE WHEN cm.metric_name = '{m}' THEN cm.value END) AS {m}"
            for m in metrics
        ]
        select_clause = ",\n        ".join(case_expressions)

        query = text(f"""
            SELECT
                cm.timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'UTC' AS timestamp,
                cm.dimensions->>'region' AS region,
                {select_clause}
            FROM canonical_metrics cm
            WHERE cm.metric_name = ANY(:metrics)
              AND cm.timestamp >= :cutoff
              AND cm.dimensions ? 'region'
            GROUP BY timestamp, cm.dimensions->>'region'
            ORDER BY timestamp DESC
        """)

        df_raw = pd.read_sql(query, engine, params={"cutoff": cutoff, "metrics": metrics}) # type: ignore

        get_cache().setex(key, CACHE_TTL, df_raw.to_json(orient="split"))
        return df_raw.copy()

    except Exception as e:
        logger.error(f"Ошибка загрузки данных из БД: {e}")
        regions_df = pd.read_csv(settings.data_regions_path)
        regions_df["error"] = True
        regions_df["error_message"] = str(e)
        return regions_df
```
### 📄 `core/database.py`

```python
# core/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from config import settings, get_database_url
import logging
import threading
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("db")

_engine = None
_engine_lock = threading.Lock()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OperationalError)
)
def get_engine():
    global _engine

    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        database_url = str(get_database_url())

        pool_size = getattr(settings, "DB_POOL_SIZE", 20)
        max_overflow = getattr(settings, "DB_MAX_OVERFLOW", 40)

        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "options": "-c statement_timeout=30000",
                "connect_timeout": 10,
            }
        )

        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info(f"SQLAlchemy engine initialized (pool_size={pool_size}, max_overflow={max_overflow})")

    return _engine

```
### 📄 `core/exceptions.py`

```python
# core/exceptions.py
"""
Иерархия исключений для Situational Center

✅ Преимущества:
- Специфичная обработка ошибок
- Улучшенное логирование
- Правильные HTTP статусы
- Контекст для debugging
"""

from typing import Optional, Dict, Any


class SituationalCenterError(Exception):
    """Базовое исключение проекта"""
    
    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для API ответов"""
        return {
            "error": self.code,
            "message": self.message,
            "context": self.context
        }


# === Database Errors ===

class DatabaseError(SituationalCenterError):
    """Ошибки работы с БД"""
    pass


class DuplicateAlertError(DatabaseError):
    """Попытка создать дубликат алерта"""
    
    def __init__(self, fingerprint: str, existing_id: Optional[str] = None):
        super().__init__(
            f"Alert with fingerprint {fingerprint} already exists",
            code="DUPLICATE_ALERT",
            context={"fingerprint": fingerprint, "existing_id": existing_id}
        )
        self.fingerprint = fingerprint
        self.existing_id = existing_id


class DatabaseUnavailableError(DatabaseError):
    """БД временно недоступна"""
    
    def __init__(self, original_error: Exception):
        super().__init__(
            "Database temporarily unavailable",
            code="DB_UNAVAILABLE",
            context={"original_error": str(original_error)}
        )
        self.original_error = original_error


class QueryTimeoutError(DatabaseError):
    """Таймаут выполнения запроса"""
    
    def __init__(self, query: str, timeout_seconds: int):
        super().__init__(
            f"Query timed out after {timeout_seconds}s",
            code="QUERY_TIMEOUT",
            context={"query": query[:100], "timeout": timeout_seconds}
        )


# === Cache Errors ===

class CacheError(SituationalCenterError):
    """Ошибки работы с кэшем (Redis)"""
    pass


class CacheConnectionError(CacheError):
    """Не удалось подключиться к Redis"""
    
    def __init__(self, host: str, port: int):
        super().__init__(
            f"Failed to connect to Redis at {host}:{port}",
            code="CACHE_CONNECTION_ERROR",
            context={"host": host, "port": port}
        )


class CacheLockTimeoutError(CacheError):
    """Таймаут получения distributed lock"""
    
    def __init__(self, lock_name: str, timeout: float):
        super().__init__(
            f"Failed to acquire lock '{lock_name}' within {timeout}s",
            code="LOCK_TIMEOUT",
            context={"lock_name": lock_name, "timeout": timeout}
        )


# === ML Errors ===

class MLModelError(SituationalCenterError):
    """Ошибки ML-моделей"""
    pass


class ModelTrainingError(MLModelError):
    """Ошибка обучения модели"""
    
    def __init__(
        self,
        metric_name: str,
        method: str,
        reason: str
    ):
        super().__init__(
            f"Failed to train {method} model for {metric_name}: {reason}",
            code="MODEL_TRAINING_ERROR",
            context={"metric": metric_name, "method": method, "reason": reason}
        )


class InsufficientDataError(MLModelError):
    """Недостаточно данных для обучения"""
    
    def __init__(self, metric_name: str, required: int, actual: int):
        super().__init__(
            f"Insufficient data for {metric_name}: need {required}, got {actual}",
            code="INSUFFICIENT_DATA",
            context={"metric": metric_name, "required": required, "actual": actual}
        )


class ModelNotFoundError(MLModelError):
    """Модель не найдена в кэше"""
    
    def __init__(self, metric_name: str, region: str):
        super().__init__(
            f"No trained model for {metric_name} in {region}",
            code="MODEL_NOT_FOUND",
            context={"metric": metric_name, "region": region}
        )


# === Alert Errors ===

class AlertError(SituationalCenterError):
    """Ошибки системы алертов"""
    pass


class AlertSendError(AlertError):
    """Не удалось отправить уведомление"""
    
    def __init__(self, channel: str, reason: str):
        super().__init__(
            f"Failed to send alert via {channel}: {reason}",
            code="ALERT_SEND_ERROR",
            context={"channel": channel, "reason": reason}
        )


class RateLimitExceededError(AlertError):
    """Превышен лимит отправки алертов"""
    
    def __init__(self, limit: int, window: int):
        super().__init__(
            f"Rate limit exceeded: {limit} alerts per {window}s",
            code="RATE_LIMIT_EXCEEDED",
            context={"limit": limit, "window": window}
        )


# === Configuration Errors ===

class ConfigurationError(SituationalCenterError):
    """Ошибки конфигурации"""
    pass


class MetricNotFoundError(ConfigurationError):
    """Метрика не найдена в metadata"""
    
    def __init__(self, metric_name: str):
        super().__init__(
            f"Metric '{metric_name}' not found or inactive",
            code="METRIC_NOT_FOUND",
            context={"metric_name": metric_name}
        )


class InvalidDimensionError(ConfigurationError):
    """Недопустимое измерение"""
    
    def __init__(self, dimension: str, allowed: list):
        super().__init__(
            f"Dimension '{dimension}' not allowed. Allowed: {allowed}",
            code="INVALID_DIMENSION",
            context={"dimension": dimension, "allowed": allowed}
        )


# === Validation Errors ===

class ValidationError(SituationalCenterError):
    """Ошибки валидации данных"""
    pass


class TimeRangeError(ValidationError):
    """Неверный временной диапазон"""
    
    def __init__(self, reason: str):
        super().__init__(
            f"Invalid time range: {reason}",
            code="TIME_RANGE_ERROR",
            context={"reason": reason}
        )


class InputSizeLimitError(ValidationError):
    """Превышен лимит размера входных данных"""
    
    def __init__(self, input_type: str, limit: int, actual: int):
        super().__init__(
            f"{input_type} size {actual} exceeds limit {limit}",
            code="INPUT_SIZE_LIMIT",
            context={"type": input_type, "limit": limit, "actual": actual}
        )

class InvalidDimensionKeyError(ConfigurationError):
    """Недопустимый ключ измерения (попытка инъекции)"""
    def __init__(self, key: str):
        super().__init__(
            f"Invalid dimension key: '{key}'. Must match ^[a-zA-Z0-9_\-]{{1,50}}$", # type: ignore
            code="INVALID_DIMENSION_KEY",
            context={"key": key}
        )

# === API Error Handlers ===
# Используйте в api/main.py

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, DatabaseError as SQLADatabaseError
import logging

logger = logging.getLogger(__name__)


async def situational_center_error_handler(
    request: Request,
    exc: SituationalCenterError
) -> JSONResponse:
    """Обработчик всех кастомных исключений"""
    
    # Определяем HTTP статус по типу ошибки
    status_codes = {
        DatabaseUnavailableError: 503,
        QueryTimeoutError: 504,
        CacheConnectionError: 503,
        CacheLockTimeoutError: 408,
        DuplicateAlertError: 409,
        MetricNotFoundError: 404,
        ModelNotFoundError: 404,
        ValidationError: 400,
        InvalidDimensionError: 400,
        TimeRangeError: 400,
        InputSizeLimitError: 413,
        RateLimitExceededError: 429,
        AlertSendError: 502,
        ModelTrainingError: 500,
        InsufficientDataError: 400,
    }
    
    status_code = status_codes.get(type(exc), 500)
    
    # Логируем в зависимости от severity
    if status_code >= 500:
        logger.error(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"context": exc.context, "request_path": request.url.path}
        )
    else:
        logger.warning(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"context": exc.context}
        )
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLADatabaseError
) -> JSONResponse:
    """Обработчик ошибок SQLAlchemy"""
    
    # Конвертируем в наши исключения
    if isinstance(exc, IntegrityError):
        logger.warning(f"Integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "error": "CONFLICT",
                "message": "Data conflict (duplicate or constraint violation)"
            }
        )
    
    if isinstance(exc, OperationalError):
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "DB_UNAVAILABLE",
                "message": "Database temporarily unavailable"
            }
        )
    
    # Общая ошибка БД
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "DB_ERROR",
            "message": "Database error occurred"
        }
    )
    

```
### 📄 `core/idoit_service.py`

```python
# core/idoit_service.py
"""
Bidirectional i-doit integration service.

i-doit is the primary ITSM/CMDB system for incident resolution.
This service handles:
- Push: create/update incidents in i-doit when they change locally
- Pull: sync status changes from i-doit back to local incidents
- Mapping: priority/status translation between systems
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from config import settings, logger, mask_secrets
from core.database import get_engine
from sqlalchemy import text


# === Status/Priority mapping ===

# Sit Center -> i-doit status mapping
STATUS_TO_IDOIT = {
    "new": "1",          # New
    "in_progress": "2",  # In Progress / Open
    "escalated": "2",    # In Progress (escalated is still open in i-doit)
    "resolved": "3",     # Resolved
    "closed": "4",       # Closed
}

# i-doit -> Sit Center status mapping
STATUS_FROM_IDOIT = {
    "1": "new",
    "2": "in_progress",
    "3": "resolved",
    "4": "closed",
}

# Sit Center -> i-doit priority mapping
PRIORITY_TO_IDOIT = {
    "critical": "1",  # Very High
    "high": "2",       # High
    "medium": "3",     # Normal
    "low": "4",        # Low
}

PRIORITY_FROM_IDOIT = {
    "1": "critical",
    "2": "high",
    "3": "medium",
    "4": "low",
}


def is_enabled() -> bool:
    return bool(getattr(settings, "I_DOIT_API_URL", None) and getattr(settings, "I_DOIT_API_KEY", None))


def _call_idoit(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a JSON-RPC call to i-doit API."""
    params["apikey"] = settings.I_DOIT_API_KEY

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }

    resp = requests.post(settings.I_DOIT_API_URL, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    if result.get("error"):
        err_msg = result["error"].get("message", "unknown")
        raise RuntimeError(f"i-doit API error: {err_msg}")

    return result.get("result", {})


def _log_sync(incident_id: int, direction: str, action: str,
              payload: Any = None, response: Any = None,
              success: bool = False, error: str = None):
    """Write to idoit_sync_log for audit trail."""
    import json
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO idoit_sync_log (incident_id, direction, action, payload, response, success, error)
                    VALUES (:iid, :direction, :action, :payload, :response, :success, :error)
                """),
                {
                    "iid": incident_id,
                    "direction": direction,
                    "action": action,
                    "payload": json.dumps(payload, default=str) if payload else None,
                    "response": json.dumps(response, default=str) if response else None,
                    "success": success,
                    "error": error,
                },
            )
    except Exception as e:
        logger.error(f"Failed to write sync log: {e}")


# === Push operations (Sit Center -> i-doit) ===

def push_incident_create(incident_id: int) -> Optional[str]:
    """Create an incident in i-doit and store the external_id back."""
    if not is_enabled():
        return None

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, alert_message, description, metric, region, value,
                       priority, assigned_to, status
                FROM incidents WHERE id = :id
            """),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return None

    description = (
        f"{row['alert_message']}\n\n"
        f"Metric: {row['metric']}\n"
        f"Region: {row['region']}\n"
        f"Value: {row['value'] or 'N/A'}\n"
    )
    if row["description"]:
        description += f"\nDetails: {row['description']}"

    try:
        result = _call_idoit("cmdb.object.create", {
            "type": "C__OBJTYPE__INCIDENT",
            "title": f"[SIT-{incident_id}] {row['alert_message'][:200]}",
            "description": description,
            "status": STATUS_TO_IDOIT.get(row["status"], "1"),
            "priority": PRIORITY_TO_IDOIT.get(row["priority"], "3"),
        })

        obj_id = str(result.get("id") or result.get("objectID", ""))
        if not obj_id:
            _log_sync(incident_id, "push", "create", response=result, error="no objectID")
            return None

        external_url = f"{settings.I_DOIT_API_URL.rsplit('/api', 1)[0]}/?objID={obj_id}" if settings.I_DOIT_API_URL else None

        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE incidents SET
                        external_id = :eid, external_system = 'idoit',
                        external_url = :url, last_synced_at = :now
                    WHERE id = :id
                """),
                {"id": incident_id, "eid": obj_id, "url": external_url, "now": datetime.now(timezone.utc)},
            )

        _log_sync(incident_id, "push", "create", response=result, success=True)
        logger.info(f"i-doit incident created: SIT-{incident_id} -> idoit#{obj_id}")
        return obj_id

    except Exception as e:
        _log_sync(incident_id, "push", "create", error=mask_secrets(str(e)))
        logger.error(f"i-doit push_create failed for incident #{incident_id}: {mask_secrets(str(e))}")
        return None


def push_status_update(incident_id: int, new_status: str):
    """Sync a status change to i-doit."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    idoit_status = STATUS_TO_IDOIT.get(new_status)
    if not idoit_status:
        return

    try:
        result = _call_idoit("cmdb.object.update", {
            "id": int(row["external_id"]),
            "title": None,  # don't change title
            "status": idoit_status,
        })

        with engine.begin() as conn:
            conn.execute(
                text("UPDATE incidents SET last_synced_at = :now WHERE id = :id"),
                {"id": incident_id, "now": datetime.now(timezone.utc)},
            )

        _log_sync(incident_id, "push", "status_update",
                   payload={"status": new_status, "idoit_status": idoit_status},
                   response=result, success=True)

    except Exception as e:
        _log_sync(incident_id, "push", "status_update", error=mask_secrets(str(e)))
        logger.warning(f"i-doit status sync failed for #{incident_id}: {mask_secrets(str(e))}")


def push_assignment(incident_id: int, assigned_to: str):
    """Sync an assignment change to i-doit."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    try:
        result = _call_idoit("cmdb.object.update", {
            "id": int(row["external_id"]),
            "assigned": assigned_to,
        })
        _log_sync(incident_id, "push", "assign",
                   payload={"assigned_to": assigned_to}, response=result, success=True)
    except Exception as e:
        _log_sync(incident_id, "push", "assign", error=mask_secrets(str(e)))
        logger.warning(f"i-doit assign sync failed for #{incident_id}: {mask_secrets(str(e))}")


def push_comment(incident_id: int, author: str, content: str):
    """Push a comment to i-doit as a logbook entry."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    try:
        result = _call_idoit("cmdb.logbook.create", {
            "object_id": int(row["external_id"]),
            "message": f"[{author}] {content}",
            "description": content,
        })
        _log_sync(incident_id, "push", "comment",
                   payload={"author": author}, response=result, success=True)
    except Exception as e:
        _log_sync(incident_id, "push", "comment", error=mask_secrets(str(e)))
        logger.warning(f"i-doit comment sync failed for #{incident_id}: {mask_secrets(str(e))}")


# === Pull operations (i-doit -> Sit Center) ===

def pull_status_update(incident_id: int, idoit_status: str, idoit_assigned: str = None):
    """
    Apply a status change from i-doit to the local incident.
    Called from the inbound webhook handler.
    """
    local_status = STATUS_FROM_IDOIT.get(str(idoit_status))
    if not local_status:
        logger.warning(f"Unknown i-doit status '{idoit_status}' for incident #{incident_id}")
        return

    engine = get_engine()
    now = datetime.now(timezone.utc)

    updates = ["status = :status", "last_synced_at = :now"]
    params: Dict[str, Any] = {"id": incident_id, "status": local_status, "now": now}

    if local_status == "in_progress":
        updates.append("started_at = COALESCE(started_at, :now)")
    elif local_status == "resolved":
        updates.append("resolved_at = COALESCE(resolved_at, :now)")
    elif local_status == "closed":
        updates.append("closed_at = COALESCE(closed_at, :now)")

    if idoit_assigned:
        updates.append("assigned_to = :assigned")
        params["assigned"] = idoit_assigned

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE incidents SET {', '.join(updates)} WHERE id = :id"),
            params,
        )

    _log_sync(incident_id, "pull", "status_update",
              payload={"idoit_status": idoit_status, "local_status": local_status},
              success=True)
    logger.info(f"i-doit pull: incident #{incident_id} -> {local_status}")

```
### 📄 `core/kafka_consumer.py`

```python
# core/kafka_consumer.py
import json
import time
from typing import List, Dict, Any
from kafka import KafkaConsumer
from sqlalchemy import text
from config import settings, logger, mask_secrets
from core.database import get_engine

TOPIC = "sit_center.metrics"
BATCH_SIZE = 100
POLL_TIMEOUT_MS = 1000


class MetricKafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str = "sit-center-ingest"):
        self.consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=False,
            max_poll_records=BATCH_SIZE,
        )
        self.engine = get_engine()
        logger.info("Kafka consumer initialized for topic: %s", TOPIC)

    def run(self):
        logger.info("Kafka consumer started")
        try:
            while True:
                self._poll_and_insert()
        except KeyboardInterrupt:
            logger.info("Kafka consumer shutting down")
        finally:
            self.consumer.close()

    def _poll_and_insert(self):
        messages = self.consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
        batch: List[Dict[str, Any]] = []

        for tp, records in messages.items():
            for record in records:
                msg = record.value
                batch.append({
                    "metric_name": msg["metric_name"],
                    "value": msg["value"],
                    "timestamp": msg.get("timestamp"),
                    "dimensions": json.dumps(msg.get("dimensions", {})),
                    "tags": json.dumps(msg.get("tags", {})),
                    "source": msg.get("source", "kafka"),
                })

                if len(batch) >= BATCH_SIZE:
                    self._bulk_insert(batch)
                    batch = []

        if batch:
            self._bulk_insert(batch)

        self.consumer.commit()

    def _bulk_insert(self, batch: List[Dict[str, Any]]):
        if not batch:
            return
        insert_sql = text("""
            INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source)
            VALUES (:metric_name, :value,
                    COALESCE(:timestamp::timestamptz, NOW()),
                    :dimensions::jsonb, :tags::jsonb, :source)
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(insert_sql, batch)
            logger.debug("Inserted %d metrics from Kafka", len(batch))
        except Exception as e:
            logger.error("Kafka bulk insert failed: %s", mask_secrets(str(e)))

```
### 📄 `core/kafka_producer.py`

```python
# core/kafka_producer.py
import json
from kafka import KafkaProducer
from config import settings, logger, mask_secrets

_producer = None

TOPIC_ALERTS = "sit_center.alerts"
TOPIC_METRICS = "sit_center.metrics"


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode("utf-8"),
            acks="all",
            retries=3,
        )
    return _producer


def publish_alert_event(data: dict) -> None:
    try:
        _get_producer().send(TOPIC_ALERTS, value=data)
    except Exception as e:
        logger.error("Kafka publish_alert_event failed: %s", mask_secrets(str(e)))


def publish_metric_event(data: dict) -> None:
    try:
        _get_producer().send(TOPIC_METRICS, value=data)
    except Exception as e:
        logger.error("Kafka publish_metric_event failed: %s", mask_secrets(str(e)))

```
### 📄 `core/ldap_auth.py`

```python
# core/ldap_auth.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from config import settings, logger, mask_secrets
from sqlalchemy import text
from core.database import get_engine


@dataclass
class LDAPUser:
    username: str
    email: Optional[str]
    display_name: Optional[str]
    groups: List[str]


class LDAPAuthenticator:
    def __init__(self):
        self.url = getattr(settings, "LDAP_URL", "")
        self.base_dn = getattr(settings, "LDAP_BASE_DN", "")
        self.bind_dn = getattr(settings, "LDAP_BIND_DN", "")
        self.bind_password = getattr(settings, "LDAP_BIND_PASSWORD", "")
        self.user_search_filter = getattr(settings, "LDAP_USER_SEARCH_FILTER", "(sAMAccountName={username})")
        self.group_role_map: Dict[str, str] = getattr(settings, "LDAP_GROUP_ROLE_MAP", {})

    def authenticate(self, username: str, password: str) -> Optional[LDAPUser]:
        try:
            import ldap3
            server = ldap3.Server(self.url, get_info=ldap3.ALL)

            # Bind with service account to search
            conn = ldap3.Connection(server, user=self.bind_dn, password=self.bind_password, auto_bind=True)

            search_filter = self.user_search_filter.replace("{username}", ldap3.utils.conv.escape_filter_chars(username))
            conn.search(
                self.base_dn,
                search_filter,
                attributes=["sAMAccountName", "mail", "displayName", "memberOf"],
            )

            if not conn.entries:
                logger.info("LDAP: user '%s' not found", username)
                return None

            entry = conn.entries[0]
            user_dn = entry.entry_dn

            # Verify user password
            user_conn = ldap3.Connection(server, user=user_dn, password=password)
            if not user_conn.bind():
                logger.info("LDAP: invalid password for '%s'", username)
                return None

            groups = [str(g) for g in entry.memberOf] if hasattr(entry, "memberOf") else []
            user_conn.unbind()
            conn.unbind()

            return LDAPUser(
                username=str(entry.sAMAccountName),
                email=str(entry.mail) if hasattr(entry, "mail") else None,
                display_name=str(entry.displayName) if hasattr(entry, "displayName") else None,
                groups=groups,
            )

        except ImportError:
            logger.error("ldap3 library not installed")
            return None
        except Exception as e:
            logger.error("LDAP authentication error: %s", mask_secrets(str(e)))
            return None

    def get_roles_for_groups(self, groups: List[str]) -> List[str]:
        roles = []
        for group in groups:
            cn = group.split(",")[0].replace("CN=", "") if "CN=" in group else group
            mapped_role = self.group_role_map.get(cn)
            if mapped_role:
                roles.append(mapped_role)
        return roles or ["viewer"]

    def sync_user_to_db(self, ldap_user: LDAPUser, tenant_id: str = "default") -> None:
        engine = get_engine()
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users (username, email, tenant_id, auth_provider, is_active)
                        VALUES (:username, :email, :tenant_id, 'ldap', true)
                        ON CONFLICT (username) DO UPDATE SET
                            email = EXCLUDED.email,
                            auth_provider = 'ldap',
                            is_active = true,
                            updated_at = NOW()
                    """),
                    {
                        "username": ldap_user.username,
                        "email": ldap_user.email,
                        "tenant_id": tenant_id,
                    },
                )
            logger.info("LDAP user '%s' synced to DB", ldap_user.username)
        except Exception as e:
            logger.error("Failed to sync LDAP user: %s", mask_secrets(str(e)))


ldap_authenticator = LDAPAuthenticator()

```
### 📄 `core/locking.py`

```python
# core/locking.py
import time
import uuid
import logging
from contextlib import contextmanager
from config import settings, get_cache

logger = logging.getLogger(__name__)

# Lua-скрипт: удалить ключ только если значение совпадает (наша блокировка)
_UNLOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

@contextmanager
def global_lock(lock_name: str, timeout: float = None):  # type: ignore
    """
    Распределённая блокировка с использованием Redis (SETNX + EXPIRE).
    Безопасное освобождение через Lua-скрипт (проверка owner).
    """
    if timeout is None:
        timeout = settings.cache_locking_timeout
    lock_key = f"lock_{lock_name}"
    lock_value = str(uuid.uuid4())
    cache = get_cache()
    acquired = False
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            acquired = cache.set(lock_key, lock_value, nx=True, ex=int(timeout * 1.5))
            if acquired:
                break
            time.sleep(settings.cache_poll_interval)
        else:
            raise TimeoutError(f"Failed to acquire lock '{lock_name}' within {timeout}s")

        yield
    finally:
        if acquired:
            try:
                cache.eval(_UNLOCK_SCRIPT, 1, lock_key, lock_value)
            except Exception as e:
                logger.error(f"Error releasing lock {lock_key}: {e}")


def get_global_state(key: str, default=None):
    """Get value from global state"""
    return get_cache().get(f"global_state_{key}")


def set_global_state(key: str, value, expire=None):
    """Set value in global state"""
    get_cache().set(f"global_state_{key}", value, ex=expire)

```
### 📄 `core/metadata_service.py`

```python
# core/metadata_service.py
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import uuid
import hashlib
from sqlalchemy import text, create_engine
from config import get_cache, get_database_url, logger, mask_secrets
from core.locking import global_lock


# --- Dataclasses (DTO) ---

@dataclass
class MetricDTO:
    metric_name: str
    display_name: str
    description: Optional[str] = None
    unit: str = ""
    default_threshold: Optional[float] = None
    default_critical_threshold: Optional[float] = None
    is_active: bool = True

@dataclass
class DimensionDTO:
    dimension_key: str
    description: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    is_required: bool = False

@dataclass
class ActionDTO:
    action_type: str
    config: Dict[str, Any]
    is_active: bool = True
    id: Optional[int] = None

@dataclass
class RuleDTO:
    name: str
    condition: Dict[str, Any]  # { "expr": "...", "for": "5m", "eval": "1m" }
    labels: Dict[str, str]
    actions: List[Dict[str, Any]]
    description: Optional[str] = None
    is_active: bool = True
    id: Optional[uuid.UUID] = None

@dataclass
class MLConfigDTO:
    name: str
    metric_name: str
    group_by: List[str]
    methods: List[str]
    method_params: Dict[str, Any]
    retrain_schedule: str = "0 3 * * *"
    auto_alert: bool = True
    alert_severity: str = "warning"
    is_active: bool = True
    id: Optional[uuid.UUID] = None


# --- Сервис ---

class MetadataService:
    def __init__(self):
        self._engine = None
        self.__cache = None
        self._logger = logger.getChild("metadata_service")

    @property
    def _cache(self):
        if self.__cache is None:
            self.__cache = get_cache()
        return self.__cache

    @_cache.setter
    def _cache(self, value):
        self.__cache = value

    def _get_engine(self):
        if self._engine is None:
            self._engine = create_engine(get_database_url(), pool_pre_ping=True)
        return self._engine

    # --- Общие утилиты ---
    def _serialize_json(self, data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    def _deserialize_json(self, raw: Optional[str]) -> Any:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return raw

    def _invalidate_cache(self, prefix: str):
        """Очистка кэша по префиксу (простая реализация)"""
        # В production — использовать SCAN + DEL или Redis key prefix
        self._logger.debug(f"Кэш-инвалидация по префиксу: {prefix}")

    # --- CRUD: Metrics ---

    def create_metric(self, dto: MetricDTO, tenant_id: str = "default") -> str:
        with global_lock("metadata_metric_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_metrics (
                        metric_name, display_name, description, unit,
                        default_threshold, default_critical_threshold, is_active, tenant_id
                    ) VALUES (
                        :metric_name, :display_name, :description, :unit,
                        :default_threshold, :default_critical_threshold, :is_active, :tenant_id
                    )
                    ON CONFLICT (metric_name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        unit = EXCLUDED.unit,
                        default_threshold = EXCLUDED.default_threshold,
                        default_critical_threshold = EXCLUDED.default_critical_threshold,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING metric_name;
                """)
                params = asdict(dto)
                params["tenant_id"] = tenant_id
                with engine.begin() as conn:
                    result = conn.execute(query, params)
                    metric_name = result.scalar_one()
                    self._invalidate_cache("metrics")
                    self._logger.info(f"Метрика '{metric_name}' создана/обновлена (tenant={tenant_id})")
                    return metric_name
            except Exception as e:
                self._logger.error(f"Ошибка создания метрики {dto.metric_name}: {mask_secrets(str(e))}")
                raise

    def get_metric(self, metric_name: str, tenant_id: str = "default") -> Optional[MetricDTO]:
        key = f"metadata:metric:{tenant_id}:{metric_name}"
        cached = self._cache.get(key)
        if cached:
            return MetricDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text(
                "SELECT * FROM metadata_metrics "
                "WHERE metric_name = :name AND is_active = true AND tenant_id = :tid"
            )
            with engine.connect() as conn:
                row = conn.execute(query, {"name": metric_name, "tid": tenant_id}).mappings().first()
                if not row:
                    return None
                dto = MetricDTO(**{k: row[k] for k in MetricDTO.__dataclass_fields__})
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"Ошибка чтения метрики {metric_name}: {mask_secrets(str(e))}")
            return None

    def list_metrics(self, active_only: bool = True, tenant_id: str = "default") -> List[MetricDTO]:
        key = f"metadata:metrics:{tenant_id}:{'active' if active_only else 'all'}"
        cached = self._cache.get(key)
        if cached:
            return [MetricDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            conditions = ["tenant_id = :tenant_id"]
            if active_only:
                conditions.append("is_active = true")
            where = "WHERE " + " AND ".join(conditions)
            query = text(f"SELECT * FROM metadata_metrics {where} ORDER BY metric_name")
            with engine.connect() as conn:
                rows = conn.execute(query, {"tenant_id": tenant_id}).mappings().all()
                dtos = [MetricDTO(**{k: row[k] for k in MetricDTO.__dataclass_fields__}) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"Ошибка списка метрик: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Dimensions ---

    def create_dimension(self, dto: DimensionDTO, tenant_id: str = "default") -> str:
        with global_lock("metadata_dimension_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_dimensions (
                        dimension_key, description, allowed_values, is_required, tenant_id
                    ) VALUES (
                        :dimension_key, :description, :allowed_values, :is_required, :tenant_id
                    )
                    ON CONFLICT (dimension_key) DO UPDATE SET
                        description = EXCLUDED.description,
                        allowed_values = EXCLUDED.allowed_values,
                        is_required = EXCLUDED.is_required,
                        created_at = NOW()
                    RETURNING dimension_key;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "dimension_key": dto.dimension_key,
                        "description": dto.description,
                        "allowed_values": self._serialize_json(dto.allowed_values),
                        "is_required": dto.is_required,
                        "tenant_id": tenant_id,
                    })
                    dim_key = result.scalar_one()
                    self._invalidate_cache("dimensions")
                    self._logger.info(f"Измерение '{dim_key}' создано/обновлено (tenant={tenant_id})")
                    return dim_key
            except Exception as e:
                self._logger.error(f"Ошибка создания измерения {dto.dimension_key}: {mask_secrets(str(e))}")
                raise

    def get_dimension(self, dimension_key: str, tenant_id: str = "default") -> Optional[DimensionDTO]:
        key = f"metadim:{tenant_id}:{dimension_key}"
        cached = self._cache.get(key)
        if cached:
            return DimensionDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text(
                "SELECT * FROM metadata_dimensions WHERE dimension_key = :key AND tenant_id = :tid"
            )
            with engine.connect() as conn:
                row = conn.execute(query, {"key": dimension_key, "tid": tenant_id}).mappings().first()
                if not row:
                    return None
                dto = DimensionDTO(**{k: row[k] for k in DimensionDTO.__dataclass_fields__})
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"Ошибка чтения измерения {dimension_key}: {mask_secrets(str(e))}")
            return None

    def list_dimensions(self, tenant_id: str = "default") -> List[DimensionDTO]:
        key = f"metadimensions:{tenant_id}:all"
        cached = self._cache.get(key)
        if cached:
            return [DimensionDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text(
                "SELECT * FROM metadata_dimensions WHERE tenant_id = :tid ORDER BY dimension_key"
            )
            with engine.connect() as conn:
                rows = conn.execute(query, {"tid": tenant_id}).mappings().all()
                dtos = [DimensionDTO(**{k: row[k] for k in DimensionDTO.__dataclass_fields__}) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"Ошибка списка измерений: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Rules ---

    def create_rule(self, dto: RuleDTO, tenant_id: str = "default") -> uuid.UUID:
        rule_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_rule_{rule_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_rules (
                        id, name, description, condition, labels, actions, is_active, tenant_id
                    ) VALUES (
                        :id, :name, :description, :condition, :labels, :actions, :is_active, :tenant_id
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        condition = EXCLUDED.condition,
                        labels = EXCLUDED.labels,
                        actions = EXCLUDED.actions,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING id;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "id": rule_id,
                        "name": dto.name,
                        "description": dto.description,
                        "condition": self._serialize_json(dto.condition),
                        "labels": self._serialize_json(dto.labels),
                        "actions": self._serialize_json(dto.actions),
                        "is_active": dto.is_active,
                        "tenant_id": tenant_id,
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("rules")
                    self._logger.info(f"Правило '{dto.name}' (id={created_id}) создано/обновлено")
                    return created_id
            except Exception as e:
                self._logger.error(f"Ошибка создания правила {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_rules(self, tenant_id: str = "default") -> List[RuleDTO]:
        key = f"metadata:rules:{tenant_id}:active"
        cached = self._cache.get(key)
        if cached:
            return [RuleDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules
                WHERE is_active = true AND tenant_id = :tid
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query, {"tid": tenant_id}).mappings().all()
                dtos = []
                for row in rows:
                    dto = RuleDTO(
                        id=row["id"],
                        name=row["name"],
                        description=row["description"],
                        condition=self._deserialize_json(row["condition"]),
                        labels=self._deserialize_json(row["labels"]),
                        actions=self._deserialize_json(row["actions"]),
                        is_active=row["is_active"]
                    )
                    dtos.append(dto)
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"Ошибка списка правил: {mask_secrets(str(e))}")
            return []

    # --- CRUD: ML Configs ---

    def create_ml_config(self, dto: MLConfigDTO, tenant_id: str = "default") -> uuid.UUID:
        config_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_ml_{config_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_ml_configs (
                        id, name, metric_name, group_by, methods, method_params,
                        retrain_schedule, auto_alert, alert_severity, is_active, tenant_id
                    ) VALUES (
                        :id, :name, :metric_name, :group_by, :methods, :method_params,
                        :retrain_schedule, :auto_alert, :alert_severity, :is_active, :tenant_id
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        metric_name = EXCLUDED.metric_name,
                        group_by = EXCLUDED.group_by,
                        methods = EXCLUDED.methods,
                        method_params = EXCLUDED.method_params,
                        retrain_schedule = EXCLUDED.retrain_schedule,
                        auto_alert = EXCLUDED.auto_alert,
                        alert_severity = EXCLUDED.alert_severity,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING id;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "id": config_id,
                        "name": dto.name,
                        "metric_name": dto.metric_name,
                        "group_by": dto.group_by,
                        "methods": dto.methods,
                        "method_params": self._serialize_json(dto.method_params),
                        "retrain_schedule": dto.retrain_schedule,
                        "auto_alert": dto.auto_alert,
                        "alert_severity": dto.alert_severity,
                        "is_active": dto.is_active,
                        "tenant_id": tenant_id,
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("ml_configs")
                    self._logger.info(f"ML-конфиг '{dto.name}' (id={created_id}) создан/обновлён")
                    return created_id
            except Exception as e:
                self._logger.error(f"Ошибка создания ML-конфига {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_ml_configs(self, tenant_id: str = "default") -> List[MLConfigDTO]:
        key = f"metadata:ml_configs:{tenant_id}:active"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                       retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                WHERE is_active = true AND tenant_id = :tid
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query, {"tid": tenant_id}).mappings().all()
                dtos = []
                for row in rows:
                    dto = MLConfigDTO(
                        id=row["id"],
                        name=row["name"],
                        metric_name=row["metric_name"],
                        group_by=row["group_by"],
                        methods=row["methods"],
                        method_params=self._deserialize_json(row["method_params"]),
                        retrain_schedule=row["retrain_schedule"],
                        auto_alert=row["auto_alert"],
                        alert_severity=row["alert_severity"],
                        is_active=row["is_active"]
                    )
                    dtos.append(dto)
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"Ошибка списка ML-конфигов: {mask_secrets(str(e))}")
            return []

    def list_all_ml_configs(self, tenant_id: str = "default") -> List[MLConfigDTO]:
        key = f"metaml_configs:{tenant_id}:all"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                    retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                WHERE tenant_id = :tid
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query, {"tid": tenant_id}).mappings().all()
                dtos = [MLConfigDTO(
                    id=row["id"],
                    name=row["name"],
                    metric_name=row["metric_name"],
                    group_by=row["group_by"],
                    methods=row["methods"],
                    method_params=self._deserialize_json(row["method_params"]),
                    retrain_schedule=row["retrain_schedule"],
                    auto_alert=row["auto_alert"],
                    alert_severity=row["alert_severity"],
                    is_active=row["is_active"]
                ) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"Ошибка списка всех ML-конфигов: {mask_secrets(str(e))}")
            return []

    # --- Утилиты ---

    @staticmethod
    def make_fingerprint(metric_name: str, dimensions: Dict[str, str], rule_id: Optional[uuid.UUID] = None) -> str:
        """Генерирует стабильный fingerprint для подавления дублей"""
        parts = [metric_name] + sorted([f"{k}={v}" for k, v in dimensions.items()])
        if rule_id:
            parts.append(str(rule_id))
        return hashlib.md5(":".join(parts).encode()).hexdigest()



# Экземпляр сервиса — синглтон
metadata_service = MetadataService()

def get_or_create_default_ml_configs(metric_name: str) -> List[MLConfigDTO]:
    configs = [c for c in metadata_service.list_active_ml_configs() if c.metric_name == metric_name]
    if not configs:
        return [MLConfigDTO(
            name=f"Auto-{metric_name}",
            metric_name=metric_name,
            group_by=["region"],
            methods=["prophet"],
            method_params={},
            is_active=True,
            id=None
        )]
    return configs

```
### 📄 `core/metric_service.py`

```python
# core/metric_service.py
from typing import List, Dict, Optional
from config import logger, get_cache, mask_secrets
from dataclasses import dataclass
from core.locking import global_lock
import json
from dataclasses import asdict

@dataclass
class Metric:
    column: str
    display_name: str
    threshold: int
    priority: int
    weight: float
    is_active: bool
    
    def __post_init__(self):
        if not isinstance(self.threshold, int):
            self.threshold = int(self.threshold)
        if not isinstance(self.priority, int):
            self.priority = int(self.priority)

# Глобальная переменная для кэширования
_METRICS_CACHE = None
_LAST_CACHE_UPDATE = 0
_CACHE_TTL = 300  # 5 минут

def get_config_service():
    """Ленивая загрузка config_service"""
    from core import config_service
    return config_service

def load_metrics_from_db(force_refresh: bool = False) -> List[Metric]:
    """
    Загружает активные метрики из БД через универсальный ConfigService.
    Использует кэширование Redis.
    """

    try:
        # Получаем сырые данные из универсального сервиса
        raw_metrics = get_config_service().get("metrics") # type: ignore

        # Фильтруем только активные и конвертируем в объекты Metric
        metrics = []
        for row in raw_metrics:
            if not row.get("is_active", True):
                continue
            metric = Metric(
                column=row["column_name"],
                display_name=row["display_name"],
                threshold=row["threshold"],
                priority=row["priority"],
                weight=row.get("weight", 1.0),
                is_active=True
            )
            metrics.append(metric)

        logger.info(f"✅ Загружено {len(metrics)} активных метрик через ConfigService")
        return metrics

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки метрик через ConfigService: {mask_secrets(str(e))}")
        # Fallback — минимальный набор
        return [
            Metric(
                column="complaints",
                display_name="Жалобы",
                threshold=4,
                priority=1,
                weight=1.0,
                is_active=True
            )
        ]

# Удаляем декоратор lru_cache и создаем простую функцию-обертку
def load_metrics_from_db_cached():
    cache = get_cache()
    key = "config:metrics"

    # Попробуем получить из кэша
    cached_data = cache.get(key)
    if cached_data is not None:
        try:
            # Десериализуем и восстанавливаем объекты Metric
            metrics_data = json.loads(cached_data) # type: ignore
            metrics = [Metric(**item) for item in metrics_data]
            return metrics
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Ошибка чтения кэша метрик: {mask_secrets(str(e))}")

    # Если кэш пуст — захватываем лок
    with global_lock("load_metrics", timeout=10):
        # Повторная проверка после захвата лока (double-checked locking)
        cached_data = cache.get(key)
        if cached_data is not None:
            try:
                metrics_data = json.loads(cached_data) # type: ignore
                metrics = [Metric(**item) for item in metrics_data]
                return metrics
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Ошибка чтения кэша метрик под локом: {mask_secrets(str(e))}")

        # Загружаем свежие данные
        metrics = load_metrics_from_db(force_refresh=True)  # ← Получаем объекты
        if not metrics:
            logger.error("Не удалось загрузить метрики из БД")
            return []

        # Сериализуем объекты в JSON для сохранения в Redis
        try:
            metrics_data = [asdict(m) for m in metrics]  # dataclass → dict
            cache.setex(key, 300, json.dumps(metrics_data, ensure_ascii=False))
            logger.info(f"✅ Загружено {len(metrics)} активных метрик через ConfigService")
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик в кэш: {mask_secrets(str(e))}")

        return metrics

def get_metric_by_column(col: str) -> Optional[Metric]:
    metrics = load_metrics_from_db_cached()
    return next((m for m in metrics if m.column == col), None)

def get_metric_buttons() -> Dict[str, tuple]:
    """Возвращает словарь для кнопок (btn-id -> (label, column))"""
    metrics = load_metrics_from_db_cached()
    return {
        f"btn-{m.column}": (m.display_name, m.column)
        for m in metrics
    }

# Добавляем функцию для принудительного обновления кэша
def refresh_metrics_cache():
    """Принудительно обновляет кэш метрик"""
    global _METRICS_CACHE, _LAST_CACHE_UPDATE
    _METRICS_CACHE = None
    _LAST_CACHE_UPDATE = 0
    return load_metrics_from_db(force_refresh=True)
```
### 📄 `core/ml_anomaly.py`

```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import logging
import joblib
from config import get_cache, settings, logger, mask_secrets
from core.metric_service import load_metrics_from_db_cached
from core.database import get_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from core.models import MLAnomaly, MetadataMLConfig, MetadataMetric
from core.metadata_service import MLConfigDTO, metadata_service, get_or_create_default_ml_configs
from core.utils import serialize_anomalies
from tenacity import retry, stop_after_attempt, wait_exponential
import psutil  # Для мониторинга памяти
import gc
try:
    import tensorflow as tf
    from prophet import Prophet
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from tensorflow.keras.models import Sequential 
    from tensorflow.keras.layers import LSTM, Dense
    from sklearn.cluster import DBSCAN
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logger.warning("ML libraries missing — anomaly detection disabled")

from contextlib import contextmanager
import re
import sys
import os
import torch

SAFE_DIMENSION_KEY_RE = re.compile(r"^[a-zA-Z0-9_]{1,50}$")
from pathlib import Path

ML_MODEL_DIR = Path("/app/models")
logger = logging.getLogger(__name__)
device = 'cuda' if torch.cuda.is_available() else 'cpu'


# Ключи кэша
MODEL_CACHE_KEY = "ml_model_{metric}_{region}"
ANOMALY_CACHE_KEY = "ml_last_anomaly_{metric}_{region}"

# Порог уверенности аномалии (Isolation Forest)
ANOMALY_THRESHOLD = -0.5

# Минимальное количество точек для обучения
MIN_POINTS = 48

def _get_model_path(metric_name: str, group_key: str) -> Path:
    ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in f"{metric_name}_{group_key}")
    return ML_MODEL_DIR / f"{safe_key}.pkl"

def save_model(model, metric_name: str, group_key: str) -> str:
    path = _get_model_path(metric_name, group_key)
    try:
        joblib.dump(model, path)
        version = f"{int(datetime.now().timestamp())}"
        return version
    except Exception as e:
        logger.error(f"❌ Не удалось сохранить модель {path}: {e}")
        raise

def load_model(metric_name: str, group_key: str) -> Optional[Any]:
    path = _get_model_path(metric_name, group_key)
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки {path}: {e}")
        return None

@contextmanager
def suppress_stdout():
    """Подавляет stdout (Prophet слишком болтлив)"""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def detect_anomaly_prophet_isolation(
    df: pd.DataFrame,
    metric_col: str,
    region_col: str = "region",
    ts_col: str = "timestamp"
) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    """
    Обнаружение аномалий: Prophet (остатки) + Isolation Forest.
    Возвращает список аномальных точек с меткой времени и регионом.
    """
    anomalies = []
    cache = get_cache()  # Получаем кэш один раз перед циклом

    for region in df[region_col].unique():
        region_data = df[df[region_col] == region].copy()
        if len(region_data) < MIN_POINTS:
            continue

        # Подготовка данных для Prophet
        prophet_df = region_data[[ts_col, metric_col]].rename(
            columns={ts_col: "ds", metric_col: "y"}
        )
        if prophet_df["ds"].dt.tz is not None:
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
        prophet_df = prophet_df.dropna().sort_values("ds")

        if len(prophet_df) < MIN_POINTS:
            continue

        # Убираем дубликаты по времени (если есть)
        prophet_df = prophet_df.groupby("ds").agg({"y": "mean"}).reset_index()

        try:
            # Prophet: модель с ежечасной сезонностью
            model = Prophet( # type: ignore
                daily_seasonality=True, # type: ignore
                weekly_seasonality=True, # type: ignore
                yearly_seasonality=False, # type: ignore
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            model.fit(prophet_df)
            
            # Предсказание и остатки
            forecast = model.predict(prophet_df[["ds"]])
            prophet_df["yhat"] = forecast["yhat"].values
            prophet_df["residual"] = prophet_df["y"] - prophet_df["yhat"]
            prophet_df["abs_residual"] = prophet_df["residual"].abs()

            # Isolation Forest на остатках + значение y
            features = prophet_df[["y", "abs_residual"]].values
            iso_forest = IsolationForest(contamination=0.1, random_state=42) # type: ignore
            anomaly_labels = iso_forest.fit_predict(features)  # 1 = норма, -1 = аномалия

            # Сохраняем модель
            model_key = MODEL_CACHE_KEY.format(metric=metric_col, region=region)
            model_bytes = joblib.dumps(model) # type: ignore
            cache.set(model_key, model_bytes, ex=60 * 60 * 24 * 7)  # 7 дней вместо 24 часов

            # Фильтруем аномалии
            anomalous_points = prophet_df[anomaly_labels == -1]
            for _, row in anomalous_points.iterrows():
                anomalies.append({
                    "region": region,
                    "metric": metric_col,
                    "timestamp": row["ds"].to_pydatetime(),
                    "value": row["y"],
                    "predicted": row["yhat"],
                    "residual": row["residual"]
                })

        except Exception as e:
            logger.error(f"ML anomaly failed for {region}/{metric_col}: {mask_secrets(str(e))}", exc_info=True)
            raise  

    return anomalies


def find_recent_ml_anomalies(time_filter="6h", metrics=None, methods=None):
    if methods is None:
        methods = settings.ml_methods or ["prophet", "lstm", "clustering"]

    delta_map = {"1h": 1, "6h": 6, "24h": 24, "2d": 48, "5d": 120}
    hours = delta_map.get(time_filter, 6)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    engine = get_engine()

    active_metrics = {m.metric_name for m in metadata_service.list_metrics(active_only=True)}
    target_metrics = set(metrics) if metrics else active_metrics

    query_base = """
        SELECT
            metric_name,
            value,
            timestamp,
            dimensions,
            tags
        FROM canonical_metrics
        WHERE metric_name = ANY(:metrics)
          AND timestamp >= :cutoff
        ORDER BY timestamp
    """

    # Пагинация
    rows = []
    offset = 0
    batch_size = 10000
    with engine.connect() as conn:
        while True:
            batch_query = text(query_base + " OFFSET :offset LIMIT :batch_size")
            batch = conn.execute(batch_query, {
                "metrics": list(target_metrics),
                "cutoff": cutoff,
                "offset": offset,
                "batch_size": batch_size
            }).mappings().all()
            if not batch:
                break
            rows.extend(batch)
            offset += batch_size

    if not rows:
        logger.warning(f"Нет данных за {time_filter} для метрик: {target_metrics}")
        return []

    df = pd.DataFrame(rows)
    df = df[df["value"].between(df["value"].quantile(0.01), df["value"].quantile(0.99))]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    if df.empty:
        return []

    df["dimensions"] = df["dimensions"].apply(lambda x: x if isinstance(x, dict) else {})
    df["tags"] = df["tags"].apply(lambda x: x if isinstance(x, dict) else {})

    all_anomalies = []

    max_workers = min(settings.ML_MAX_WORKERS or 4, os.cpu_count() or 4)

    for metric in target_metrics:
        metric_df = df[df["metric_name"] == metric]
        if metric_df.empty:
            continue

        ml_configs = [cfg for cfg in metadata_service.list_active_ml_configs() if cfg.metric_name == metric]
        ml_configs = ml_configs or get_or_create_default_ml_configs(metric)

        for cfg in ml_configs:
            try:
                group_by = cfg.group_by or ["region"]
                group_by = [g for g in group_by if metric_df["dimensions"].apply(lambda d: g in d).any()]

                if not group_by:
                    groups = [("all", metric_df)]
                else:
                    def extract_key(row):
                        return tuple(row["dimensions"].get(k, "N/A") for k in group_by)
                    
                    metric_df["_group_key"] = metric_df.apply(extract_key, axis=1)
                    groups = list(metric_df.groupby("_group_key"))
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    process_func = partial(process_group_batch, cfg=cfg)
                    futures = []
                    for group_key, group_df in groups:
                        if psutil.virtual_memory().percent > 80:
                            logger.warning(f"High memory ({psutil.virtual_memory().percent}%) — skipping {group_key}")
                            continue
                        futures.append(executor.submit(process_func, (group_key, group_df)))
                    
                    for future in as_completed(futures):
                        try:
                            anomalies = future.result(timeout=60)
                            all_anomalies.extend(anomalies)
                        except TimeoutError:
                            logger.warning("Timeout processing group")
                        except Exception as e:
                            logger.error(f"Error processing group: {mask_secrets(str(e))}")
            
            except Exception as e:
                logger.error(f"Ошибка ML для {metric}, group={cfg.group_by}: {mask_secrets(str(e))}")

    if all_anomalies:
        Session = sessionmaker(bind=engine)
        with Session() as session:
            try:
                for a in all_anomalies:
                    anomaly = MLAnomaly(
                        metric_name=a["metric_name"],
                        dimensions=a["dimensions"],
                        timestamp=a["timestamp"],
                        value=a["value"],
                        predicted=a.get("predicted"),
                        residual=a.get("residual"),
                        confidence=a.get("confidence"),
                        method=a["method"]
                    )
                    session.add(anomaly)
                session.commit()
                logger.info(f"✅ Сохранено {len(all_anomalies)} ML-аномалий")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения: {mask_secrets(str(e))}")
                session.rollback()

    get_cache().set("ml_anomalies", serialize_anomalies(all_anomalies), ex=300)
    return all_anomalies


# Вспомогательные функции для групп
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def detect_anomaly_prophet_isolation_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    
    # Подготовка данных для Prophet
    prophet_df = df[["timestamp", "value"]].rename(
        columns={"timestamp": "ds", "value": "y"}
    ).copy()
    
    # Корректная обработка timezone
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    
    # Prophet требует tz-naive, но сохраняем смысл времени
    if prophet_df["ds"].dt.tz is not None:
        prophet_df["ds"] = prophet_df["ds"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Сортировка и удаление дубликатов
    prophet_df = prophet_df.dropna().sort_values("ds")
    prophet_df = prophet_df.drop_duplicates(subset="ds", keep="last")
    
    if len(prophet_df) < MIN_POINTS:
        return []
    
    try:
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )
        
        with suppress_stdout():
            model.fit(prophet_df)

        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            if len(prophet_df) >= 100:
                with suppress_stdout():
                    df_cv = cross_validation(
                        model,
                        initial='15 days',
                        period='3 days',
                        horizon='7 days',
                        parallel="processes"
                    )
                    df_perf = performance_metrics(df_cv)
                
                cv_mape = df_perf['mape'].mean()
                if cv_mape > 0.3:
                    logger.warning(f"CV MAPE={cv_mape:.1%} >30% для {dimensions} — модель ненадежна")
                    return []
                logger.info(f"✅ CV MAPE={cv_mape:.1%} для {dimensions}")
        except ImportError:
            logger.debug("prophet.diagnostics недоступен — пропуск CV")
        except Exception as e:
            logger.warning(f"Ошибка кросс-валидации: {e}")

        forecast = model.predict(prophet_df[["ds"]])
        prophet_df["yhat"] = forecast["yhat"].values
        prophet_df["yhat_lower"] = forecast["yhat_lower"].values
        prophet_df["yhat_upper"] = forecast["yhat_upper"].values
        prophet_df["residual"] = prophet_df["y"] - prophet_df["yhat"]
        prophet_df["abs_residual"] = prophet_df["residual"].abs()
        
        mape = np.mean(np.abs((prophet_df["y"] - prophet_df["yhat"]) / prophet_df["y"])) * 100
        if mape > 30:
            logger.warning(f"Prophet MAPE={mape:.1f}% >30% для {dimensions} — пропуск")
            return []
        
        features = prophet_df[["y", "abs_residual"]].values
        iso = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        labels = iso.fit_predict(features)
        
        anomalies = []
        for idx, row in prophet_df[labels == -1].iterrows():
            ts = pd.Timestamp(row["ds"], tz="UTC")
            anomalies.append({
                "timestamp": ts.to_pydatetime(),
                "value": float(row["y"]),
                "predicted": float(row["yhat"]),
                "residual": float(row["residual"]),
                "confidence": float(iso.decision_function(features)[idx])
            })
        
        return anomalies
    
    except Exception as e:
        logger.warning(f"Prophet failed для {dimensions}: {e}")
        raise

def detect_anomaly_lstm_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    
    # Ограничение памяти
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            logger.warning(f"GPU memory setup failed: {e}")
    
    if len(df) < 48:
        return []
    
    values = df['value'].values.reshape(-1, 1)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)

    def create_sequences(data, seq_length=24):
        xs, ys = [], []
        for i in range(len(data) - seq_length):
            xs.append(data[i:(i + seq_length)])
            ys.append(data[i + seq_length])
        return np.array(xs), np.array(ys)

    seq_length = 24
    X, y = create_sequences(scaled, seq_length)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = None

    model = Sequential([
        LSTM(50, activation='relu', input_shape=(seq_length, 1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    try:
        model.fit(X, y, epochs=10, verbose=0, batch_size=32)
        predictions = model.predict(X, verbose=0)
        mse = np.mean(np.power(y - predictions, 2), axis=1)
        threshold = np.mean(mse) + 3 * np.std(mse)

        anomalies = []
        for i in range(len(mse)):
            if mse[i] > threshold:
                anomalies.append({
                    'timestamp': df.iloc[i + seq_length]['timestamp'],
                    'value': values[i + seq_length][0],
                    'predicted': scaler.inverse_transform(predictions[i].reshape(-1, 1))[0][0],
                    'residual': mse[i],
                    'confidence': 1 - (mse[i] - np.min(mse)) / (np.max(mse) - np.min(mse)) if np.max(mse) > np.min(mse) else 0.5
                })
        return anomalies
    except Exception as e:
        logger.error(f"LSTM detection failed: {e}")
        return []
    finally:
        # Обязательная очистка
        if model:
            del model
        tf.keras.backend.clear_session()
        gc.collect()

def detect_anomaly_clustering_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []    

    lat = dimensions.get("lat")
    lon = dimensions.get("lon")
    if not (lat and lon):
        return []

    if 'value' not in df.columns or len(df) < 3:
        return []

    # Предполагаем, что df имеет lat/lon в dimensions, но для group — агрегируем? Или per-row
    # Адаптируем: Добавим lat/lon в df если нужно, но поскольку dimensions — для группы, пропустим или используйте coords из data
    # Пример: Если df имеет 'lat', 'lon'
    if 'lat' not in df.columns or 'lon' not in df.columns:
        return []

    df = df.dropna(subset=['lat', 'lon', 'value'])

    coords = df[['lat', 'lon']].values
    values = df['value'].values.reshape(-1, 1)

    X = np.hstack([coords, values * 0.1])  # Scale

    clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
    labels = clustering.labels_

    anomalies = []
    for i, label in enumerate(labels):
        if label == -1:
            row = df.iloc[i]
            anomalies.append({
                'timestamp': row['timestamp'],
                'value': row['value'],
                'predicted': None,  # No predicted in clustering
                'residual': None,
                'confidence': clustering.core_sample_indices_[i] if i in clustering.core_sample_indices_ else 0,
                'method': 'clustering'
            })
    return anomalies


def get_ml_model_status() -> Dict[str, List[str]]:
    """
    Возвращает статус обученных моделей (для дебага/админки).
    """
    cache = get_cache()
    metrics = [m.column for m in load_metrics_from_db_cached()]
    regions = cache.get("regions") or ["Moscow", "SPb"]  # или загрузить из БД

    trained = []
    for m in metrics:
        for r in regions: # type: ignore
            key = MODEL_CACHE_KEY.format(metric=m, region=r)
            if cache.get(key):
                trained.append(f"{m} → {r}")
    return {"trained_models": trained}

def detect_anomaly_lstm(region_data, metric_col, window_size=24):
    if not HAS_ML_LIBS:
        return []    
    """Обнаружение аномалий с помощью LSTM"""
    try:
        # Подготовка данных
        values = region_data[metric_col].values
        if len(values) < window_size * 2:
            return []
        
        # Нормализация
        scaler = StandardScaler()
        scaled_values = scaler.fit_transform(values.reshape(-1, 1)).flatten()
        
        # Создание окон данных
        X, y = [], []
        for i in range(len(scaled_values) - window_size):
            X.append(scaled_values[i:i+window_size])
            y.append(scaled_values[i+window_size])
        
        X, y = np.array(X), np.array(y)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Построение модели LSTM
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(window_size, 1)),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        
        # Обучение модели
        model.fit(X, y, epochs=10, verbose=0)
        
        # Прогнозирование
        predictions = model.predict(X, verbose=0)
        
        # Вычисление ошибок прогнозирования
        errors = np.abs(y - predictions.flatten())
        
        # Определение аномалий (ошибка > 2 стандартных отклонения)
        threshold = np.mean(errors) + 2 * np.std(errors)
        anomalies = []
        
        for i in range(len(errors)):
            if errors[i] > threshold:
                anomalies.append({
                    'timestamp': region_data.iloc[i+window_size]['timestamp'],
                    'value': values[i+window_size],
                    'predicted': scaler.inverse_transform([[predictions[i][0]]])[0][0],
                    'error': errors[i]
                })
        
        return anomalies
        
    except Exception as e:
        logger.warning(f"LSTM anomaly detection failed: {e}")
        return []

def detect_anomaly_clustering(df: pd.DataFrame, metric_col: str) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []    

    # Проверим, есть ли lat/lon в df
    if 'lat' not in df.columns or 'lon' not in df.columns:
        logger.warning("Нет координат 'lat'/'lon' в данных. Пропуск кластеризации.")
        return []

    # Фильтруем только строки с данными
    df = df.dropna(subset=['lat', 'lon', metric_col])

    if len(df) < 3:
        return []

    coords = df[['lat', 'lon']].values
    values = df[metric_col].values.reshape(-1, 1) # type: ignore

    # Объединяем координаты и значения
    X = np.hstack([coords, values * 0.1])  # масштабируем значение

    clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
    labels = clustering.labels_

    anomalies = []
    for i, label in enumerate(labels):
        if label == -1:  # шум = аномалия
            row = df.iloc[i]
            anomalies.append({
                'region': row['region'],
                'metric': metric_col,
                'timestamp': row['timestamp'],
                'value': row[metric_col],
                'lat': row['lat'],
                'lon': row['lon'],
                'cluster_method': 'DBSCAN'
            })
    return anomalies
    
    
def retrain_all_models():
    logger.info("Начало переобучения ML-моделей")
    engine = get_engine()
    Session = sessionmaker(bind=engine)

    if not HAS_ML_LIBS:
        return []    

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.ml_model_cache_days)

    with Session() as session:
        # Загружаем активные ML-конфиги
        ml_configs = (
            session.query(MetadataMLConfig)
            .join(MetadataMetric)
            .filter(
                MetadataMLConfig.is_active.is_(True),
                MetadataMetric.is_active.is_(True)
            )
            .all()
        )

        if not ml_configs:
            logger.info("Нет активных ML-конфигураций для переобучения.")
            return

        for cfg in ml_configs:
            metric_name = cfg.metric_name
            group_by_keys = cfg.group_by or ["region"]

            # Валидация dimension keys для защиты от SQL injection
            for key in group_by_keys:
                if not SAFE_DIMENSION_KEY_RE.match(key):
                    logger.error(f"Invalid dimension key: {key}, skipping config {cfg.id}")
                    continue

            logger.info(f"Переобучение: {metric_name}, group_by={group_by_keys}")

            # Безопасное построение запроса: ключи валидированы regex выше
            dim_select = ", ".join(
                f"dimensions->>'{key}' as \"{key}\"" for key in group_by_keys
            )
            dim_filter = " AND ".join(
                f"dimensions->>'{key}' IS NOT NULL" for key in group_by_keys
            )

            query = text(f"""
            SELECT
                timestamp,
                value,
                {dim_select}
            FROM canonical_metrics
            WHERE metric_name = :metric_name
              AND timestamp >= :cutoff
              AND {dim_filter}
            ORDER BY timestamp
            LIMIT 10000
            """)

            df = pd.read_sql(
                query,
                engine,
                params={"metric_name": metric_name, "cutoff": cutoff}
            )

            if df.empty:
                logger.info(f"Нет данных для {metric_name}")
                continue

            # Группируем по group_by
            group_cols = [col for col in group_by_keys if col in df.columns]
            if not group_cols:
                continue

            for group_tuple, group_df in df.groupby(group_cols):
                if len(group_df) < MIN_POINTS:
                    continue

                # Приводим к формату Prophet
                prophet_df = group_df[["timestamp", "value"]].copy()
                prophet_df = prophet_df.rename(columns={"timestamp": "ds", "value": "y"})
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
                prophet_df = prophet_df.dropna().sort_values("ds")

                if len(prophet_df) < MIN_POINTS:
                    continue

                try:
                    model = Prophet(
                        daily_seasonality=True,
                        weekly_seasonality=True,
                        yearly_seasonality=False,
                        changepoint_prior_scale=0.05,
                        seasonality_prior_scale=10.0
                    )
                    model.fit(prophet_df)

                    # Формируем ключ кэша
                    group_key = "_".join(str(v) for v in group_tuple) if isinstance(group_tuple, tuple) else str(group_tuple)
                    cache_key = f"ml_model:{metric_name}:{group_key}"

                    cache = get_cache()
                    cache.set(cache_key, joblib.dumps(model), ex=60*60*24*settings.ml_model_cache_days)

                    logger.info(f"Модель переобучена: {cache_key}")

                except Exception as e:
                    logger.error(f"Ошибка обучения модели {metric_name}/{group_key}: {e}")

    logger.info("Переобучение ML-моделей завершено")

def process_group_batch(group_data: tuple, cfg: MLConfigDTO) -> List[Dict]:
    """
    Обрабатывает одну группу данных для ML-аномалий.
    
    Args:
        group_data: (group_key, group_df)
        cfg: ML-конфигурация
    
    Returns:
        Список аномалий
    """
    group_key, group_df = group_data
    
    if len(group_df) < MIN_POINTS:
        return []
    
    dims = dict(zip(cfg.group_by, group_key)) if cfg.group_by else {}
    all_anomalies = []
    
    try:
        # Prophet
        if "prophet" in cfg.methods:
            anomalies = detect_anomaly_prophet_isolation_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "prophet"
                })
            all_anomalies.extend(anomalies)
        
        # LSTM
        if "lstm" in cfg.methods and len(group_df) >= 48:
            anomalies = detect_anomaly_lstm_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "lstm"
                })
            all_anomalies.extend(anomalies)
        
        # Clustering
        if "clustering" in cfg.methods and "lat" in dims and "lon" in dims:
            anomalies = detect_anomaly_clustering_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "clustering"
                })
            all_anomalies.extend(anomalies)
    
    except Exception as e:
        logger.error(f"Ошибка обработки группы {dims}: {e}")
    
    return all_anomalies
```
### 📄 `core/ml_tasks.py`

```python
# core/ml_tasks.py
from celery_app import celery_app
from config import logger


@celery_app.task(time_limit=60)
def evaluate_rules_task():
    try:
        from core.rule_engine import rule_engine
        from core.notifications import notify
        results = rule_engine.evaluate_all_rules()
        fired = [r for r in results if r.fired]
        for r in fired:
            msg = f"Rule '{r.rule_name}': {r.metric_name} {r.operator} {r.threshold} (current: {r.current_value:.2f})"
            notify(msg, "warning")
        logger.info("Rule evaluation: %d rules checked, %d fired", len(results), len(fired))
        return {"checked": len(results), "fired": len(fired)}
    except Exception as e:
        logger.exception("Rule evaluation failed")
        return {"error": str(e)}


@celery_app.task(queue="ml", time_limit=600)
def run_ml_anomaly_check():
    try:
        from core.ml_anomaly import find_recent_ml_anomalies
        count = find_recent_ml_anomalies(time_filter="6h")
        logger.info(f"ML: found {count} anomalies")
        return count
    except Exception as e:
        logger.exception("ML task failed")
        return 0


@celery_app.task(queue="ml", time_limit=600)
def retrain_ml_models():
    try:
        from core.ml_anomaly import retrain_all_models
        retrain_all_models()
        return {"status": "success"}
    except Exception as e:
        logger.exception("Retrain ML failed")
        return {"status": "error", "message": str(e)}

```
### 📄 `core/models.py`

```python
# core/models.py

from sqlalchemy import Column, Integer, String, DateTime, Float, Index, func, JSON, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import enum
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass


# === Каноническая метрика (только для ORM-запросов, необязательна, но удобна) ===
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String, default="local")
    external_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    roles = relationship("Role", secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    permissions = Column(JSONB, nullable=False, default=list)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    users = relationship("User", secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class CanonicalMetric(Base):
    __tablename__ = "canonical_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    dimensions = Column(JSONB, nullable=False, default=dict)
    tags = Column(JSONB, nullable=False, default=dict)
    source = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")

    __table_args__ = (
        Index("ix_canonical_ts", "timestamp"),
        Index("ix_canonical_metric", "metric_name"),
        Index("ix_canonical_dims_gin", "dimensions", postgresql_using="gin"),
        Index("ix_canonical_tags_gin", "tags", postgresql_using="gin"),
    )


# === Другие модели (остаются без изменений, кроме удаления Monitoring) ===

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    column_name = Column(String, unique=True, nullable=False)  # ← legacy alias! будет устаревать
    display_name = Column(String, nullable=False)
    threshold = Column(Integer, nullable=False, default=1)
    priority = Column(Integer, nullable=False, default=1)
    weight = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_metrics_column_name", "column_name"),
        Index("ix_metrics_is_active", "is_active"),
    )


class MLAnomaly(Base):
    __tablename__ = "ml_anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ml_config_id = Column(UUID(as_uuid=True), nullable=True)  # ← связь с metadata_ml_configs
    metric_name = Column(String, nullable=False)
    dimensions = Column(JSONB, nullable=False, default=dict)  # ← вместо region
    timestamp = Column(DateTime(timezone=True), nullable=False)
    value = Column(Float, nullable=False)
    predicted = Column(Float)
    residual = Column(Float)
    confidence = Column(Float)
    method = Column(String, default="prophet")  # prophet, lstm, clustering
    model_version = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        dims = ", ".join(f"{k}={v}" for k, v in self.dimensions.items())
        return f"<MLAnomaly {self.metric_name}[{dims}]={self.value} @ {self.timestamp}>"


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=True)
    ml_config_id = Column(UUID(as_uuid=True), nullable=True)
    metric_name = Column(String, nullable=False)
    dimensions = Column(JSONB, nullable=False, default=dict)
    value = Column(Float, nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    detected_at = Column(DateTime(timezone=True), default=func.now())
    status = Column(String, default="firing")  # firing, acknowledged, resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    fingerprint = Column(String, nullable=False, index=True)
    escalation_level = Column(Integer, default=0)
    last_escalation = Column(DateTime(timezone=True), nullable=True)
    alert_hash = Column(String, index=True)
    tenant_id = Column(String, nullable=False, default="default")

    incident_created = Column(Boolean, default=False)
    incident_created_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_alerts_firing", "status", postgresql_where=(status == "firing")),
        Index("ix_alerts_fingerprint", "fingerprint"),
    )

class IncidentStatus(enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_message = Column(Text, nullable=False)
    metric = Column(String, nullable=False)
    region = Column(String, nullable=False)
    value = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, default=IncidentStatus.NEW.value)
    detected_at = Column(DateTime(timezone=True), default=func.now())
    assigned_to = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")
    description = Column(Text, nullable=True)
    alert_event_id = Column(UUID(as_uuid=True), nullable=True)
    sla_policy_id = Column(UUID(as_uuid=True), ForeignKey("sla_policies.id"), nullable=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    resolution_deadline = Column(DateTime(timezone=True), nullable=True)
    response_breached = Column(Boolean, default=False)
    resolution_breached = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    escalation_chain_id = Column(UUID(as_uuid=True), ForeignKey("escalation_chains.id"), nullable=True)
    last_escalated_at = Column(DateTime(timezone=True), nullable=True)
    external_id = Column(String, nullable=True)
    external_system = Column(String, default="idoit")
    external_url = Column(String, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    incident = relationship("Incident", back_populates="comments")


class ConfigTable(Base):
    __tablename__ = "config_tables"

    name = Column(String, primary_key=True)
    model_class = Column(String, nullable=False)
    cache_key = Column(String, nullable=False)
    ttl = Column(Integer, default=300)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    schema_name = Column(String, default="public")
    
class MetadataMetric(Base):
    __tablename__ = "metadata_metrics"

    metric_name = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(Text)
    unit = Column(String, default="")
    default_threshold = Column(Float)
    default_critical_threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # В классе MetadataMetric — добавьте:
    ml_configs = relationship("MetadataMLConfig", back_populates="metric", cascade="all, delete-orphan")

class MetadataDimension(Base):
    __tablename__ = "metadata_dimensions"

    dimension_key = Column(String, primary_key=True)
    description = Column(Text)
    allowed_values = Column(JSONB)
    is_required = Column(Boolean, default=False)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())

class MetadataRule(Base):
    __tablename__ = "metadata_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    condition = Column(JSONB, nullable=False)
    labels = Column(JSONB, default=dict)
    actions = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
class MetadataMLConfig(Base):
    __tablename__ = "metadata_ml_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    metric_name = Column(String, ForeignKey("metadata_metrics.metric_name"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")
    group_by = Column(ARRAY(String), nullable=False, default=list)  # TEXT[] → ARRAY(String)
    methods = Column(ARRAY(String), nullable=False, default=lambda: ["prophet"])
    method_params = Column(JSONB, nullable=False, default=dict)
    retrain_schedule = Column(String, default="0 3 * * *")
    auto_alert = Column(Boolean, default=True)
    alert_severity = Column(String, default="warning")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Связи
    metric = relationship("MetadataMetric", back_populates="ml_configs")


class SlaPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    name = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    response_time_minutes = Column(Integer, nullable=False)
    resolution_time_minutes = Column(Integer, nullable=False)
    escalation_after_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


class EscalationChain(Base):
    __tablename__ = "escalation_chains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    levels = relationship("EscalationLevel", back_populates="chain", cascade="all, delete-orphan", order_by="EscalationLevel.level")


class EscalationLevel(Base):
    __tablename__ = "escalation_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id = Column(UUID(as_uuid=True), ForeignKey("escalation_chains.id", ondelete="CASCADE"), nullable=False)
    level = Column(Integer, nullable=False)
    notify_role = Column(String, nullable=False)
    notify_users = Column(JSONB, default=list)
    escalate_after_minutes = Column(Integer, nullable=False)
    chain = relationship("EscalationChain", back_populates="levels")
```
### 📄 `core/notifications.py`

```python
# core/notifications.py
import signal
import sys
from config import logger, mask_secrets
from celery_app import celery_app
from tenacity import retry, stop_after_attempt, wait_fixed

class NotificationError(Exception):
    pass

# безопасно отправляем задачу без top-level импорта tasks
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def notify(message: str, priority: str = "info") -> None:
    try:
        celery_app.send_task("tasks.send_notification", args=[message, priority], kwargs={})
        logger.debug(f"📨 Уведомление отправлено в Celery: [{priority}] {message[:80]}...")
        try:
            from api.main import ALERTS_SENT
            ALERTS_SENT.labels(priority=priority).inc()
        except Exception:
            pass
    except Exception as e:
        logger.exception("❌ Ошибка при отправке уведомления в Celery")
        raise NotificationError(f"Failed to send notification: {mask_secrets(str(e))}")

# graceful shutdown handler — использует telegram helper (lazy import inside function)
def _shutdown_handler(signum, frame):
    logger.info(f"🛑 Получен сигнал {signal.strsignal(signum)} — graceful shutdown...")
    try:
        from telegram_bot import close_telegram_session_sync
        close_telegram_session_sync()
    except Exception:
        logger.debug("Не удалось закрыть Telegram session")
    logger.info("✅ Завершение работы.")
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT, _shutdown_handler)

logger.info("✅ Модуль уведомлений инициализирован")

```
### 📄 `core/oidc_auth.py`

```python
# core/oidc_auth.py
from authlib.integrations.starlette_client import OAuth
from config import settings, logger

oauth = OAuth()


def configure_oidc():
    """Register the OIDC provider (Keycloak) with authlib OAuth."""
    if not getattr(settings, "OIDC_ENABLED", False):
        return

    issuer_url = getattr(settings, "OIDC_ISSUER_URL", "")
    client_id = getattr(settings, "OIDC_CLIENT_ID", "")
    client_secret = getattr(settings, "OIDC_CLIENT_SECRET", "")

    if not all([issuer_url, client_id, client_secret]):
        logger.warning("OIDC enabled but missing configuration; skipping")
        return

    oauth.register(
        name="keycloak",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url=f"{issuer_url}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    logger.info("OIDC provider 'keycloak' registered (issuer=%s)", issuer_url)

```
### 📄 `core/pubsub.py`

```python
# core/pubsub.py
import json
import redis
import redis.asyncio as aioredis
from config import settings, logger, mask_secrets

ALERT_CHANNEL = "sit_center:alerts"


def _get_redis_url() -> str:
    if settings.REDIS_URL:
        return settings.REDIS_URL
    pwd = settings.REDIS_PASSWORD or ""
    return f"redis://:{pwd}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


def publish_alert(data: dict) -> None:
    """Publish an alert to Redis Pub/Sub (sync, for Celery/alerts)."""
    try:
        r = redis.from_url(_get_redis_url(), decode_responses=True)
        r.publish(ALERT_CHANNEL, json.dumps(data, ensure_ascii=False, default=str))
        r.close()
    except Exception as e:
        logger.error(f"Failed to publish alert: {mask_secrets(str(e))}")


async def subscribe_alerts(callback):
    """Subscribe to alert channel and invoke callback for each message (async, for WS)."""
    while True:
        try:
            r = aioredis.from_url(_get_redis_url(), decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(ALERT_CHANNEL)
            logger.info("Subscribed to Redis Pub/Sub channel: %s", ALERT_CHANNEL)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await callback(data)
                    except Exception as e:
                        logger.warning(f"Error processing pubsub message: {e}")

        except Exception as e:
            logger.error(f"Redis Pub/Sub connection error: {mask_secrets(str(e))}")
            import asyncio
            await asyncio.sleep(5)
        finally:
            try:
                await pubsub.unsubscribe(ALERT_CHANNEL)
                await r.aclose()
            except Exception:
                pass

```
### 📄 `core/rbac.py`

```python
# core/rbac.py
from fastapi import Depends, HTTPException
from api.auth import get_current_user, TokenData


def require_permission(perm: str):
    """FastAPI dependency: require a specific permission in the JWT."""
    def _check(current_user: TokenData = Depends(get_current_user)):
        if "admin" in current_user.scopes:
            return current_user
        if perm not in current_user.permissions:
            raise HTTPException(403, f"Missing permission: {perm}")
        return current_user
    return _check


def require_role(role: str):
    """FastAPI dependency: require a specific role in the JWT."""
    def _check(current_user: TokenData = Depends(get_current_user)):
        if "admin" in current_user.scopes:
            return current_user
        if role not in current_user.roles:
            raise HTTPException(403, f"Missing role: {role}")
        return current_user
    return _check

```
### 📄 `core/resilience.py`

```python
# core/resilience.py
"""Graceful degradation helpers: Redis fallback, i-doit retry queue."""
import functools
from config import logger


def redis_fallback(default=None):
    """Decorator: if Redis is unavailable, return default instead of crashing."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Redis unavailable in {func.__name__}, returning fallback: {e}")
                return default() if callable(default) else default
        return wrapper
    return decorator


def safe_idoit_push(func):
    """Decorator: swallow i-doit push errors so they never crash callers.
    Logs to sync_log and enqueues for retry via Celery."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"i-doit push failed in {func.__name__}: {e}. Will retry via Celery.")
            try:
                from celery_app import celery_app
                celery_app.send_task(
                    "tasks.retry_idoit_push",
                    args=[func.__name__, args, kwargs],
                    countdown=60,
                )
            except Exception as retry_err:
                logger.error(f"Failed to enqueue i-doit retry: {retry_err}")
            return None
    return wrapper

```
### 📄 `core/rule_engine.py`

```python
# core/rule_engine.py
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine
from core.metadata_service import metadata_service, RuleDTO


@dataclass
class ParsedCondition:
    metric_name: str
    labels: Dict[str, str]
    operator: str
    threshold: float


@dataclass
class EvalResult:
    rule_id: str
    rule_name: str
    metric_name: str
    dimensions: Dict[str, str]
    current_value: float
    threshold: float
    operator: str
    fired: bool


_CONDITION_RE = re.compile(
    r'^([a-zA-Z0-9_\-\.]+)'       # metric name
    r'(?:\{([^}]*)\})?'           # optional {label='val', ...}
    r'\s*([><=!]+)\s*'            # operator
    r'([\d.]+)$'                  # threshold
)

_ALLOWED_OPS = {">", "<", ">=", "<=", "==", "!="}


class PromQLParser:
    @staticmethod
    def parse(expr: str) -> Optional[ParsedCondition]:
        expr = expr.strip()
        m = _CONDITION_RE.match(expr)
        if not m:
            logger.warning("Failed to parse rule expression: %s", expr)
            return None

        metric_name, labels_str, operator, threshold_str = m.groups()

        if operator not in _ALLOWED_OPS:
            logger.warning("Invalid operator in rule: %s", operator)
            return None

        labels: Dict[str, str] = {}
        if labels_str:
            for pair in labels_str.split(","):
                pair = pair.strip()
                if "=" not in pair:
                    continue
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if re.match(r'^[a-zA-Z0-9_\-]{1,50}$', k):
                    labels[k] = v

        return ParsedCondition(
            metric_name=metric_name,
            labels=labels,
            operator=operator,
            threshold=float(threshold_str),
        )


class RuleEngine:
    def __init__(self):
        self.parser = PromQLParser()

    def evaluate_all_rules(self) -> List[EvalResult]:
        rules = metadata_service.list_active_rules()
        results: List[EvalResult] = []

        for rule in rules:
            try:
                rule_results = self._evaluate_rule(rule)
                results.extend(rule_results)
            except Exception as e:
                logger.error("Error evaluating rule %s: %s", rule.name, mask_secrets(str(e)))

        return results

    def _evaluate_rule(self, rule: RuleDTO) -> List[EvalResult]:
        condition = rule.condition
        expr = condition.get("expr") if isinstance(condition, dict) else getattr(condition, "expr", None)
        if not expr:
            return []

        parsed = self.parser.parse(expr)
        if not parsed:
            return []

        # Query the latest values for this metric, grouped by dimensions
        engine = get_engine()
        where_parts = ["metric_name = :metric_name", "timestamp >= NOW() - INTERVAL '5 minutes'"]
        params: Dict[str, Any] = {"metric_name": parsed.metric_name}

        for i, (k, v) in enumerate(parsed.labels.items()):
            where_parts.append(f"dimensions->>:key_{i} = :val_{i}")
            params[f"key_{i}"] = k
            params[f"val_{i}"] = v

        query = text(f"""
            SELECT dimensions, AVG(value) AS avg_value
            FROM canonical_metrics
            WHERE {" AND ".join(where_parts)}
            GROUP BY dimensions
            LIMIT 1000
        """)

        results: List[EvalResult] = []
        try:
            with engine.connect() as conn:
                rows = conn.execute(query, params).mappings().all()

            for row in rows:
                avg_val = float(row["avg_value"])
                fired = _compare(avg_val, parsed.operator, parsed.threshold)
                results.append(EvalResult(
                    rule_id=str(rule.id),
                    rule_name=rule.name,
                    metric_name=parsed.metric_name,
                    dimensions=row["dimensions"] or {},
                    current_value=avg_val,
                    threshold=parsed.threshold,
                    operator=parsed.operator,
                    fired=fired,
                ))
        except Exception as e:
            logger.error("Rule evaluation query failed for %s: %s", rule.name, mask_secrets(str(e)))

        return results


def _compare(value: float, op: str, threshold: float) -> bool:
    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    return ops.get(op, lambda a, b: False)(value, threshold)


rule_engine = RuleEngine()

```
### 📄 `core/sla_service.py`

```python
# core/sla_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from sqlalchemy import text
from core.database import get_engine
from config import logger


def get_sla_policy(tenant_id: str, priority: str) -> Optional[Dict]:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, response_time_minutes, resolution_time_minutes, escalation_after_minutes
                FROM sla_policies
                WHERE tenant_id = :tenant_id AND priority = :priority AND is_active = true
            """),
            {"tenant_id": tenant_id, "priority": priority},
        ).mappings().first()
        return dict(row) if row else None


def apply_sla_to_incident(incident_id: int, tenant_id: str, priority: str, detected_at: datetime):
    policy = get_sla_policy(tenant_id, priority)
    if not policy:
        return

    response_deadline = detected_at + timedelta(minutes=policy["response_time_minutes"])
    resolution_deadline = detected_at + timedelta(minutes=policy["resolution_time_minutes"])

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE incidents SET
                    sla_policy_id = :policy_id,
                    response_deadline = :response_deadline,
                    resolution_deadline = :resolution_deadline
                WHERE id = :id
            """),
            {
                "id": incident_id,
                "policy_id": policy["id"],
                "response_deadline": response_deadline,
                "resolution_deadline": resolution_deadline,
            },
        )


def check_sla_breaches():
    """Check all open incidents for SLA breaches. Called periodically by Celery."""
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.begin() as conn:
        # Response breach: incident still NEW past response deadline
        breached_response = conn.execute(
            text("""
                UPDATE incidents SET response_breached = true
                WHERE status = 'new'
                  AND response_deadline IS NOT NULL
                  AND response_deadline < :now
                  AND response_breached = false
                RETURNING id, metric, region, priority
            """),
            {"now": now},
        ).mappings().all()

        for row in breached_response:
            logger.warning(f"SLA response breach: incident #{row['id']} ({row['priority']}) {row['metric']}/{row['region']}")

        # Resolution breach: incident not resolved/closed past resolution deadline
        breached_resolution = conn.execute(
            text("""
                UPDATE incidents SET resolution_breached = true
                WHERE status NOT IN ('resolved', 'closed')
                  AND resolution_deadline IS NOT NULL
                  AND resolution_deadline < :now
                  AND resolution_breached = false
                RETURNING id, metric, region, priority
            """),
            {"now": now},
        ).mappings().all()

        for row in breached_resolution:
            logger.warning(f"SLA resolution breach: incident #{row['id']} ({row['priority']}) {row['metric']}/{row['region']}")

    return {
        "response_breaches": len(breached_response),
        "resolution_breaches": len(breached_resolution),
    }


def check_auto_escalation():
    """Auto-escalate incidents that exceeded their escalation timeout. Called by Celery."""
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.connect() as conn:
        # Find open incidents with escalation chains that need escalation
        rows = conn.execute(
            text("""
                SELECT i.id, i.escalation_level, i.escalation_chain_id,
                       i.last_escalated_at, i.detected_at, i.tenant_id,
                       i.metric, i.region, i.priority
                FROM incidents i
                WHERE i.status NOT IN ('resolved', 'closed')
                  AND i.escalation_chain_id IS NOT NULL
            """),
        ).mappings().all()

    for row in rows:
        current_level = row["escalation_level"]
        reference_time = row["last_escalated_at"] or row["detected_at"]

        with engine.connect() as conn:
            next_level = conn.execute(
                text("""
                    SELECT level, notify_role, escalate_after_minutes
                    FROM escalation_levels
                    WHERE chain_id = :chain_id AND level = :next_level
                """),
                {"chain_id": row["escalation_chain_id"], "next_level": current_level + 1},
            ).mappings().first()

        if not next_level:
            continue

        elapsed = (now - reference_time).total_seconds() / 60
        if elapsed >= next_level["escalate_after_minutes"]:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE incidents SET
                            escalation_level = :level,
                            status = 'escalated',
                            last_escalated_at = :now
                        WHERE id = :id
                    """),
                    {"id": row["id"], "level": next_level["level"], "now": now},
                )

            logger.warning(
                f"Auto-escalated incident #{row['id']} to L{next_level['level']} "
                f"({next_level['notify_role']}): {row['metric']}/{row['region']}"
            )

            try:
                from core.notifications import notify
                notify(
                    f"Escalation L{next_level['level']}: incident #{row['id']} "
                    f"{row['metric']}/{row['region']} ({row['priority']})",
                    "critical" if next_level["level"] >= 3 else "warning",
                )
            except Exception as e:
                logger.error(f"Failed to send escalation notification: {e}")

```
### 📄 `core/smart_alerts.py`

```python
# core/smart_alerts.py
import pandas as pd
from typing import Optional
from core.alert_settings import load_alert_settings_cached, AlertSettings


def check_growth_alert(df: pd.DataFrame, col: str, metric_name: str, alert_settings: AlertSettings) -> Optional[str]:
    """
    Проверяет аномальный рост метрики за короткий период.
    Использует настройки из AlertSettings.
    """
    if alert_settings is None:
        alert_settings = load_alert_settings_cached()
    settings = alert_settings
    if not settings.smart_growth_enabled:
        return None

    # Проверяем, есть ли настройки для этой метрики
    growth_config = settings.smart_growth.get(col)
    if not growth_config or df.empty or col not in df.columns:
        return None

    percent_threshold = growth_config.get("percent", 50)
    period_minutes = growth_config.get("period_minutes", 60)

    # Фильтруем данные за период
    cutoff = pd.Timestamp.now(tz=df["timestamp"].iloc[0].tz) - pd.Timedelta(minutes=period_minutes)
    recent_df = df[df["timestamp"] >= cutoff]

    if recent_df.empty or len(recent_df) < 2:
        return None

    # Группируем по регионам
    latest = recent_df.groupby("region").last()
    earliest = recent_df.groupby("region").first()

    # Вычисляем рост
    for region in latest.index:
        if region not in earliest.index:
            continue

        old_val = earliest.loc[region, col]
        new_val = latest.loc[region, col]

        if old_val == 0:
            if new_val > 0: # type: ignore
                growth_percent = 100.0
            else:
                continue
        else:
            growth_percent = ((new_val - old_val) / old_val) * 100 # type: ignore

        if growth_percent >= percent_threshold: # type: ignore
            return f"📈 Рост {metric_name}: +{growth_percent:.1f}% в регионе {region} за {period_minutes} мин"

    return None


def check_deviation_alert(df: pd.DataFrame, col: str, metric_name: str, alert_settings: AlertSettings) -> Optional[str]:
    """
    Проверяет отклонение от среднего (в std).
    """
    if alert_settings is None:
        alert_settings = load_alert_settings_cached()
    settings = alert_settings
    if not settings.smart_deviation_enabled:
        return None

    deviation_config = settings.smart_deviation.get(col)
    if not deviation_config or df.empty or col not in df.columns:
        return None

    std_threshold = deviation_config.get("std_dev", 2.0)

    values = df[col].dropna()
    if len(values) < 2:
        return None

    mean_val = values.mean()
    std_val = values.std()

    if std_val == 0:
        return None

    for _, row in df.iterrows():
        z_score = (row[col] - mean_val) / std_val
        if z_score > std_threshold:
            return f"⚠️ Отклонение {metric_name}: {row[col]} в {row['region']} (z={z_score:.2f})"

    return None
```
### 📄 `core/tenant.py`

```python
# core/tenant.py
from contextvars import ContextVar

_current_tenant: ContextVar[str] = ContextVar("current_tenant", default="default")


def get_current_tenant() -> str:
    return _current_tenant.get()


def set_current_tenant(tenant_id: str) -> None:
    _current_tenant.set(tenant_id)

```
### 📄 `core/tracing.py`

```python
# core/tracing.py
"""OpenTelemetry distributed tracing setup.

Enabled via OTEL_ENABLED=true. Exports to OTLP collector at OTEL_EXPORTER_OTLP_ENDPOINT.
If OTEL is not enabled or dependencies are missing, tracing is a no-op.
"""
import os
from config import logger


def setup_tracing(app=None):
    """Configure OpenTelemetry for FastAPI if enabled."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED != true)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Install: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-grpc "
            "opentelemetry-instrumentation-fastapi "
            "opentelemetry-instrumentation-sqlalchemy "
            "opentelemetry-instrumentation-redis "
            "opentelemetry-instrumentation-requests"
        )
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "sit-center-api")
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy
    try:
        from core.database import get_engine
        engine = get_engine()
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine if hasattr(engine, 'sync_engine') else engine)
    except Exception as e:
        logger.debug(f"SQLAlchemy instrumentation skipped: {e}")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Redis instrumentation skipped: {e}")

    # Instrument outbound HTTP (requests library — i-doit, Telegram, etc.)
    try:
        RequestsInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Requests instrumentation skipped: {e}")

    logger.info(f"OpenTelemetry tracing enabled: service={service_name}, endpoint={endpoint}")

```
### 📄 `core/utils.py`

```python
# core/utils.py
import json
from datetime import datetime
from typing import Any, List, Dict
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any: # type: ignore
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_anomalies(anomalies: List[Dict[str, Any]]) -> str:
    return json.dumps(anomalies, cls=NpEncoder, ensure_ascii=False)

def deserialize_anomalies(data_str: str) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = json.loads(data_str)
    for item in data:
        if "timestamp" in item:
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
    return data
```
### 📄 `core/vault.py`

```python
# core/vault.py
"""
HashiCorp Vault integration for secret management.

Usage:
  - Set VAULT_ENABLED=true, VAULT_ADDR, VAULT_ROLE, VAULT_SECRET_PATH in .env
  - In Kubernetes: uses Vault Agent Sidecar (annotations in Helm chart)
  - Standalone: uses AppRole or Token auth to fetch secrets at startup

Secrets from Vault override corresponding env vars in Settings.
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() == "true"
VAULT_ADDR = os.getenv("VAULT_ADDR", "https://vault.example.com")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "")
VAULT_ROLE_ID = os.getenv("VAULT_ROLE_ID", "")
VAULT_SECRET_ID = os.getenv("VAULT_SECRET_ID", "")
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "secret/data/sit-center")
VAULT_MOUNT = os.getenv("VAULT_MOUNT", "secret")


def fetch_secrets() -> Dict[str, str]:
    """Fetch secrets from Vault and return as dict of env-var-compatible keys."""
    if not VAULT_ENABLED:
        return {}

    try:
        import requests
    except ImportError:
        logger.warning("requests library required for Vault integration")
        return {}

    token = _get_vault_token()
    if not token:
        logger.error("Could not obtain Vault token")
        return {}

    try:
        headers = {"X-Vault-Token": token}
        resp = requests.get(
            f"{VAULT_ADDR}/v1/{VAULT_SECRET_PATH}",
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("data", {})
        logger.info("Fetched %d secrets from Vault", len(data))
        return data
    except Exception as e:
        logger.error("Failed to fetch secrets from Vault: %s", e)
        return {}


def _get_vault_token() -> Optional[str]:
    """Get Vault token via direct token, AppRole, or Kubernetes auth."""
    if VAULT_TOKEN:
        return VAULT_TOKEN

    # Kubernetes Service Account auth
    sa_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    if os.path.exists(sa_token_path):
        return _k8s_auth(sa_token_path)

    # AppRole auth
    if VAULT_ROLE_ID and VAULT_SECRET_ID:
        return _approle_auth()

    return None


def _k8s_auth(sa_token_path: str) -> Optional[str]:
    """Authenticate to Vault using Kubernetes service account."""
    try:
        import requests

        with open(sa_token_path) as f:
            jwt = f.read().strip()

        role = os.getenv("VAULT_ROLE", "sit-center")
        resp = requests.post(
            f"{VAULT_ADDR}/v1/auth/kubernetes/login",
            json={"jwt": jwt, "role": role},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["auth"]["client_token"]
    except Exception as e:
        logger.error("Vault Kubernetes auth failed: %s", e)
        return None


def _approle_auth() -> Optional[str]:
    """Authenticate to Vault using AppRole."""
    try:
        import requests

        resp = requests.post(
            f"{VAULT_ADDR}/v1/auth/approle/login",
            json={"role_id": VAULT_ROLE_ID, "secret_id": VAULT_SECRET_ID},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["auth"]["client_token"]
    except Exception as e:
        logger.error("Vault AppRole auth failed: %s", e)
        return None


def inject_vault_secrets():
    """Fetch secrets from Vault and inject into os.environ (before Settings init)."""
    secrets = fetch_secrets()
    for key, value in secrets.items():
        env_key = key.upper()
        if env_key not in os.environ:
            os.environ[env_key] = str(value)
            logger.debug("Injected Vault secret: %s", env_key)
        else:
            logger.debug("Vault secret %s skipped (already in env)", env_key)

```
