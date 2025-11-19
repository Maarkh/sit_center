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
│   ├────── README.md
│   ├────── celery_app.py
│   ├────── celeryconfig.py
│   ├────── config.py
│   ├────── dlq_tool.py
│   ├────── docker-compose.prod.yml
│   ├────── full_stack_architecture.txt
│   ├────── generate_data.py
│   ├────── generate_docs.py
│   ├────── init_schema.sql
│   ├────── instructions.md
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
│   │   ├────── schemas.py
│   │   ├── routes/
│   │   │   ├────── alerts.py
│   │   │   ├────── data.py
│   │   │   ├────── dimensions.py
│   │   │   ├────── metrics.py
│   │   │   ├────── ml_configs.py
│   │   │   ├────── rules.py
│   │   │   ├────── webhooks.py
│   │   │   ├────── websocket.py
│   ├── .github/
│   │   ├── workflows/
│   │   │   ├────── ci-cd.yml
│   │   │   ├────── generate-docs.yml
│   ├── db/
│   ├── alembic/
│   │   ├────── env.py
│   │   ├── versions/
│   │   │   ├────── 001_add_admin_dashboard.py
│   │   │   ├────── 002_add_metadata_ml_configs.py
│   ├── data/
│   ├── tests/
│   │   ├────── __init__.py
│   │   ├────── conftest.py
│   │   ├────── test_mask_secrets.py
│   │   ├────── test_ml.py
│   │   ├────── test_security.py
│   │   ├── integration/
│   │   │   ├────── test_end_to_end.py
│   ├── documents/
│   ├── grafana/
│   │   ├── dashboards/
│   │   ├── provisioning/
│   │   │   ├── datasources/
│   │   │   │   ├────── postgres.yaml
│   │   │   ├── dashboards/
│   │   │   │   ├────── dashboard.yml
│   ├── core/
│   │   ├────── __init__.py
│   │   ├────── alert_settings.py
│   │   ├────── alerts.py
│   │   ├────── config_service.py
│   │   ├────── data.py
│   │   ├────── database.py
│   │   ├────── exceptions.py
│   │   ├────── locking.py
│   │   ├────── metadata_service.py
│   │   ├────── metric_service.py
│   │   ├────── ml_anomaly.py
│   │   ├────── models.py
│   │   ├────── notifications.py
│   │   ├────── smart_alerts.py
│   │   ├────── utils.py
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
CMD ["celery", "-A", "tasks.celery_app", "worker", "-l", "INFO", "-P", "eventlet"]
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
    )
    return celery

def get_beat_schedule():
    from celeryconfig import beat_schedule
    return beat_schedule

celery_app = make_celery()

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
        'task': 'tasks.run_ml_anomaly_check',
        'schedule': crontab(minute='*/10')
    },
    'retrain-ml-models-daily': {
        'task': 'tasks.retrain_ml_models',
        'schedule': crontab(hour=3, minute=0)
    },
    'update-mv-10min': {
        'task': 'tasks.update_mv_data',
        'schedule': crontab(minute='*/10')
    },
    'create-partition-monthly': {
        'task': 'tasks.create_monthly_partition',
        'schedule': crontab(day_of_month=28, hour=2, minute=0)
    }
}
```
### 📄 `config.py`

```python
# config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List
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
    s = re.sub(r"(redis://[^:@]+:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)
    s = re.sub(r"(postgres(?:ql)?://[^:@]+:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)

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
    REDIS_DB: int = Field(..., env="REDIS_DB") # type: ignore
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


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
    """Корректное закрытие Redis соединения"""
    global _redis_client
    with _redis_lock:
        if _redis_client is not None:
            try:
                _redis_client.close()
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
### 📄 `docker-compose.prod.yml`

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # ——— PostgreSQL ———
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
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
    # НЕ пробрасываем порт 6379 в проде:
    # ports:
    #  - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ——— Airbyte ———
  airbyte-server:
    image: airbyte/server:latest
    environment:
      - DATABASE_PASSWORD=${POSTGRES_PASSWORD}
      - DATABASE_USER=${POSTGRES_USER}
      - DATABASE_HOST=db
      - CONFIG_DATABASE_PASSWORD=${POSTGRES_PASSWORD}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  airbyte-worker:
    image: airbyte/worker:latest
    environment:
      - DATABASE_PASSWORD=${POSTGRES_PASSWORD}
      - DATABASE_USER=${POSTGRES_USER}
      - DATABASE_HOST=db
      - WORKER_ENVIRONMENT=docker
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  airbyte-webapp:
    image: airbyte/webapp:latest
    ports:
      - "8001:80"
    depends_on:
      - airbyte-server
    networks:
      - app-network
    restart: unless-stopped

  # ——— FastAPI (единый API + Webhooks) ———
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
      test: [ "CMD", "curl", "-f", "http://localhost:8000/health" ]
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

  # ——— Celery (worker + beat) ———
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: ["celery", "-A", "tasks.celery_app", "worker", "-l", "INFO", "-P", "eventlet"]
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
      test: ["CMD", "celery", "inspect", "ping", "-b", "redis://:${REDIS_PASSWORD}@redis:6379/0"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

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
      test: ["CMD", "celery", "inspect", "ping", "-b", "redis://:${REDIS_PASSWORD}@redis:6379/0"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ——— Flower ———
  flower:
    image: mher/flower
    command: ["--broker=redis://:${REDIS_PASSWORD}@redis:6379/0", "--port=5555"]
    ports:
      - "5555:5555"
    depends_on:
      - redis
    networks:
      - app-network

  # ——— i-doit (ITSM/CMDB) ———
  idoit-mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - idoit_mysql_data:/var/lib/mysql
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$${MYSQL_ROOT_PASSWORD}"]
      timeout: 20s
      retries: 10

  idoit:
    image: i-doit/i-doit:1.19
    environment:
      DB_HOST: idoit-mysql
      DB_NAME: ${IDOIT_DB_NAME}
      DB_USER: ${IDOIT_DB_USER}
      DB_PASS: ${IDOIT_DB_PASS}
      ADMIN_PASS: ${IDOIT_ADMIN_PASS}
      ITOOL_LICENSE_KEY: ""
    ports:
      - "8080:80"
    depends_on:
      idoit-mysql:
        condition: service_healthy
    volumes:
      - idoit_data:/var/www/html
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  idoit_mysql_data:
  idoit_data:
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
### 📄 `requirements.txt`

```
aiohttp
alembic
pandas
requests
pydantic
pydantic_settings
python-docx
pathspec
diskcache
python-dotenv
pytest
pytest-mock
xlsxwriter
tenacity
psycopg2-binary
sqlalchemy
redis
fakeredis
celery
prophet
scikit-learn
joblib
tensorflow
h5py
kafka-python
fastapi
uvicorn[standard]
jose
redis
jwt
prometheus_client
slowapi
psutil
fastapi-jwt-auth
pytest-cov
torch
passlib
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
from core.ml_anomaly import find_recent_ml_anomalies
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


@celery_app.task
def run_ml_anomaly_check():
    try:
        count = find_recent_ml_anomalies(time_filter="6h")
        logger.info(f"✅ ML: найдено {count} аномалий")
        return count
    except Exception as e:
        logger.exception("❌ ML task failed")
        return 0


@celery_app.task
def retrain_ml_models():
    try:
        from core.ml_anomaly import retrain_all_models
        retrain_all_models()
        return {"status": "success"}
    except Exception as e:
        logger.exception("❌ Retrain ML failed")
        return {"status": "error", "message": str(e)}


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
                "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            }
            try:
                get_redis().xadd("dlq:notifications", payload) # type: ignore
                logger.error(f"🚨 DLQ запись: {message[:50]}...")
            except Exception as e:
                logger.exception("❌ Ошибка записи в DLQ")
    except Exception:
        logger.exception("💥 Ошибка в handle_task_failure")
        
@celery_app.task(name="tasks.create_monthly_partition", bind=True)
def create_monthly_partition(self=None):
    from sqlalchemy import text
    from core.database import get_engine
    from config import logger
    from datetime import datetime, timedelta
    import re
    """
    Создаёт партицию canonical_metrics_<YYYY_MM> на следующий месяц.
    Использует безопасный EXECUTE format('%I', table_name) внутри DO $$ ... $$.
    """
    PARTITION_NAME_RE = re.compile(r"^canonical_metrics_\d{4}_\d{2}$")
    engine = get_engine()
    today = datetime.utcnow().date()
    next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    start = next_month
    end = (start + timedelta(days=32)).replace(day=1)
    table_name = f"canonical_metrics_{next_month.strftime('%Y_%m')}"

    # Валидация имени партиции
    if not PARTITION_NAME_RE.match(table_name):
        from config import logger
        logger.error("Invalid partition name: %s", table_name)
        return

    # Используем безопасную проверку существования через to_regclass
    create_sql = text("""
    DO $$
    BEGIN
        IF to_regclass(:full_table_name) IS NULL THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF canonical_metrics FOR VALUES FROM (%L) TO (%L)',
                :table_name,
                :start_date,
                :end_date
            );
        END IF;
    END $$;
    """)

    # index creation as separate EXECUTE to avoid quoting issues
    index_sql = text("""
    DO $$
    BEGIN
        IF to_regclass(:idx_name) IS NULL THEN
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS %I ON %I (timestamp DESC)',
                :index_on_table,
                :table_name
            );
        END IF;
    END $$;
    """)

    params = {
        "full_table_name": f"public.{table_name}",
        "table_name": table_name,
        "start_date": start.strftime('%Y-%m-%d'),
        "end_date": end.strftime('%Y-%m-%d'),
        "idx_name": f"idx_{table_name}_ts",
        "index_on_table": f"idx_{table_name}_ts"
    }

    with engine.begin() as conn:
        # Создаем таблицу-партицию, если её нет
        conn.execute(create_sql, params)
        # Создаём индекс на партиции
        conn.execute(index_sql, params)

    from config import logger
    logger.info("✅ Partition %s ensured", table_name)
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
        if username is None:
            raise JWTError()
        return TokenData(username=username, scopes=scopes)
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
from sqlalchemy import create_engine
from config import get_database_url
from api.auth import get_current_user, TokenData
from fastapi import Depends, HTTPException

# Метаданные — синглтон
def get_metadata_service():
    return metadata_service

# БД (если нужно напрямую)
_engine = None
def get_db_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url())
    return _engine

def require_scope(required_scope: str):
    def _check(current_user: TokenData = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return _check
```
### 📄 `api/limiter.py`

```python
# api/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
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

from api.routes import metrics, dimensions, rules, ml_configs, alerts, data, webhooks
from api.auth import create_access_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES, OAuth2PasswordRequestForm
from datetime import timedelta
from core.exceptions import (
    situational_center_error_handler,
    sqlalchemy_error_handler,
    SituationalCenterError
)

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import DatabaseError as SQLADatabaseError
from api.limiter import limiter
from passlib.context import CryptContext

ALERTS_SENT = Counter("alerts_sent_total", "Total alerts sent", ["priority"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск API-сервера...")
    yield
    logger.info("🛑 Остановка API-сервера...")

app = FastAPI(
    title="Situational Center API",
    description="REST API для управления ситуационным центром",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
    openapi_url="/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore
app.add_exception_handler(SituationalCenterError, situational_center_error_handler) # type: ignore
app.add_exception_handler(SQLADatabaseError, sqlalchemy_error_handler) # type: ignore


# CORS (настрой под свой фронтенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← замени на ["http://localhost:8050"] в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Подключаем роутеры
app.include_router(metrics.router)
app.include_router(dimensions.router)
app.include_router(rules.router)
app.include_router(ml_configs.router)
app.include_router(alerts.router)
app.include_router(data.router)
app.include_router(webhooks.router)

# WebSocket
from api.routes.websocket import router as ws_router
app.include_router(ws_router)

# Запуск фоновой задачи WS
@app.on_event("startup")
async def startup_event():
    import asyncio
    from api.routes.websocket import alert_stream_task
    asyncio.create_task(alert_stream_task())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Проверка username
    if form_data.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Проверка пароля (хэшированного)
    if not pwd_context.verify(form_data.password, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": form_data.username, "scopes": ["admin"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
    status: Literal["firing", "resolved"]
    sent: bool
    fingerprint: str

    class Config:
        from_attributes = True
```
### 📄 `api/routes/alerts.py`

```python
# api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID
from api.schemas import AlertRead
from sqlalchemy import text
from core.database import get_engine
from api.auth import get_current_user, TokenData
from config import mask_secrets

router = APIRouter(prefix="/alerts", tags=["Alerts"])


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
        fingerprint=row["fingerprint"]
    )


@router.get("/", response_model=List[AlertRead])
def list_alerts(
    status: str = Query(None, enum=["firing", "resolved"]),
    metric_name: str = None, # type: ignore
    dimension_key: str = None, # type: ignore
    dimension_value: str = None, # type: ignore
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(get_current_user) 
):
    engine = get_engine()
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status # type: ignore
    if metric_name:
        where_clauses.append("metric_name = :metric_name")
        params["metric_name"] = metric_name # type: ignore
    if dimension_key and dimension_value:
        where_clauses.append(f"dimensions->>'{dimension_key}' = :dim_val")
        params["dim_val"] = dimension_value # type: ignore

    where = " AND ".join(where_clauses)
    if where:
        where = "WHERE " + where

    query = text(f"""
        SELECT id, rule_id, ml_config_id, metric_name, dimensions, value,
               event_time, detected_at, status, sent, fingerprint
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
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: UUID):
    engine = get_engine()
    query = text("""
        SELECT id, rule_id, ml_config_id, metric_name, dimensions, value,
               event_time, detected_at, status, sent, fingerprint
        FROM alert_events
        WHERE id = :alert_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"alert_id": alert_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")
            return _row_to_alert(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))


@router.post("/{alert_id}/suppress", status_code=204)
def suppress_alert(alert_id: UUID, minutes: int = 60, current_user: TokenData = Depends(get_current_user)):
    """Ручное подавление алерта по его fingerprint"""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT fingerprint FROM alert_events WHERE id = :id"),
                {"id": alert_id}
            ).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="Alert not found")

            from core.alerts import suppress_alert as _suppress
            _suppress(row["fingerprint"], minutes)
            return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))
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
from sqlalchemy import text
from sqlalchemy.sql import quoted_name

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
def prometheus_label_values1():
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
def prometheus_label_values(label_name: str):
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
    end: float = Query(None)
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
            where.append("dimensions->>:key_in = ANY(:vals_in)")
            params["key_in"] = k
            params["vals_in"] = clean_vals # type: ignore

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
from api.auth import get_current_user, TokenData
from config import mask_secrets

router = APIRouter(prefix="/dimensions", tags=["Dimensions"])


@router.get("/me")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=DimensionRead, status_code=status.HTTP_201_CREATED)
def create_dimension(
    data: DimensionCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        dim_key = service.create_dimension(data) # type: ignore
        dim = service.get_dimension(dim_key)
        if not dim:
            raise HTTPException(status_code=500, detail="Dimension created but not found")
        return dim
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[DimensionRead])
def list_dimensions(service: MetadataService = Depends(get_metadata_service)):
    return service.list_dimensions()


@router.get("/{dimension_key}", response_model=DimensionRead)
def get_dimension(
    dimension_key: str,
    service: MetadataService = Depends(get_metadata_service)
):
    dim = service.get_dimension(dimension_key)
    if not dim:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return dim
```
### 📄 `api/routes/metrics.py`

```python
# api/routes/metrics.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import MetricCreate, MetricRead, MetricUpdate
from core.metadata_service import MetadataService
from api.dependencies import get_metadata_service
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.post("/", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
def create_metric(
    data: MetricCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        metric_name = service.create_metric(data) # type: ignore
        metric = service.get_metric(metric_name)
        if not metric:
            raise HTTPException(status_code=500, detail="Metric created but not found")
        return metric
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[MetricRead])
def list_metrics(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service),
    current_user: TokenData = Depends(get_current_user) 
):
    return service.list_metrics(active_only=active_only)


@router.get("/{metric_name}", response_model=MetricRead)
def get_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service)
):
    metric = service.get_metric(metric_name)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.put("/{metric_name}", response_model=MetricRead)
def update_metric(
    metric_name: str,
    data: MetricUpdate,
    service: MetadataService = Depends(get_metadata_service)
):
    # Валидация: нельзя изменить имя
    if data.metric_name != metric_name:
        raise HTTPException(status_code=400, detail="Cannot change metric_name on update")
    
    try:
        # Просто вызываем create — он делает ON CONFLICT DO UPDATE
        service.create_metric(data) # type: ignore
        updated = service.get_metric(metric_name)
        if not updated:
            raise HTTPException(status_code=500, detail="Metric updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(
    metric_name: str,
    service: MetadataService = Depends(get_metadata_service)
):
    # В PostgreSQL — удаляем вручную (metadata_metrics не имеет каскада)
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM metadata_metrics WHERE metric_name = :name"),
                {"name": metric_name}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Metric not found")
        service._invalidate_cache("metrics")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))
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
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/ml/configs", tags=["ML Configs"])

@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=MLConfigRead, status_code=status.HTTP_201_CREATED)
def create_ml_config(
    service: MetadataService = Depends(get_metadata_service),
    data: MLConfigCreate = Depends()
):
    try:
        config_id = service.create_ml_config(data) # type: ignore
        config = next((c for c in service.list_active_ml_configs() if c.id == config_id), None)
        if not config:
            raise HTTPException(status_code=500, detail="Config created but not found")
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[MLConfigRead])
def list_ml_configs(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service)
):
    return service.list_active_ml_configs() if active_only else service.list_all_ml_configs()


@router.get("/{config_id}", response_model=MLConfigRead)
def get_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    configs = service.list_active_ml_configs()
    config = next((c for c in configs if c.id == config_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="ML config not found")
    return config


@router.put("/{config_id}", response_model=MLConfigRead)
def update_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service),
    data: MLConfigCreate = Depends()
):
    try:
        # Используем create_ml_config — он же делает UPSERT
        service.create_ml_config(data) # type: ignore
        updated = next((c for c in service.list_active_ml_configs() if c.id == config_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Config updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ml_config(
    config_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_ml_configs SET is_active = false WHERE id = :id"),
                {"id": config_id}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="ML config not found")
        service._invalidate_cache("ml_configs")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))
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
from api.auth import get_current_user, TokenData
from sqlalchemy import text
from config import mask_secrets

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}

@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: RuleCreate,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        rule_id = service.create_rule(data) # type: ignore
        # Перечитываем для full-объекта
        rules = service.list_active_rules() + [r for r in [] if not r.is_active]  # TODO: сделать get_rule(id)
        rule = next((r for r in rules if r.id == rule_id), None)
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        return rule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.get("/", response_model=List[RuleRead])
def list_rules(
    active_only: bool = True,
    service: MetadataService = Depends(get_metadata_service)
):
    if active_only:
        return service.list_active_rules()
    else:
        # TODO: добавить list_all_rules()
        return service.list_active_rules()


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    rules = service.list_active_rules()
    rule = next((r for r in rules if r.id == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    service: MetadataService = Depends(get_metadata_service)
):
    # Создаём DTO с id
    from dataclasses import replace
    dto = data
    # В create_rule поддерживается id
    try:
        service.create_rule(dto) # type: ignore
        updated = next((r for r in service.list_active_rules() if r.id == rule_id), None)
        if not updated:
            raise HTTPException(status_code=500, detail="Rule updated but not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(mask_secrets(str(e))))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID,
    service: MetadataService = Depends(get_metadata_service)
):
    
    engine = service._get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE metadata_rules SET is_active = false WHERE id = :id"),
                {"id": rule_id}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rule not found")
        service._invalidate_cache("rules")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(mask_secrets(str(e))))
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
    # Rate-limiting через глобальный limiter (уже настроен в main.py)
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
```
### 📄 `api/routes/websocket.py`

```python
# api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect,WebSocketException, status
from typing import List
import asyncio
import json
from core.database import get_engine
from sqlalchemy import text
from config import logger, mask_secrets
from api.auth import verify_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
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

# Фоновая задача: push новых алертов
async def alert_stream_task():
    last_ts = None
    while True:
        try:
            engine = get_engine()
            with engine.connect() as conn:
                if last_ts is None:
                    # Только последние 10 при первом запуске
                    result = conn.execute(
                        text("""
                            SELECT * FROM alert_events 
                            ORDER BY event_time DESC 
                            LIMIT 10
                        """)
                    ).mappings().all()
                else:
                    result = conn.execute(
                        text("""
                            SELECT * FROM alert_events 
                            WHERE event_time > :last_ts 
                            ORDER BY event_time ASC
                            LIMIT 50
                        """),
                        {"last_ts": last_ts}
                    ).mappings().all()
                
                if result:
                    for row in result:
                        await manager.broadcast({
                            "type": "alert",
                            "id": str(row["id"]),
                            "metric": row["metric_name"],
                            "dimensions": row["dimensions"],
                            "value": float(row["value"]),
                            "status": row["status"],
                            "event_time": row["event_time"].isoformat()
                        })
                        last_ts = row["event_time"]
                        
        except Exception as e:
            logger.error(f"WS stream error: {mask_secrets(str(e))}")
        
        await asyncio.sleep(5)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    # Получаем токен из query или headers
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
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install ruff black mypy
      - name: Run linter (Ruff)
        run: ruff check .
      - name: Run formatter (Black)
        run: black --check .
      - name: Type checking (mypy)
        run: mypy .
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ -v
  build_cpu:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Login to Docker Hub
        uses: docker/login-action@v3 # Обновлено до v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
      - name: Build CPU image
        run: |
          docker build -t Maarkh/sit_center -f Dockerfile .
      - name: Push CPU image
        run: |
          docker push Maarkh/sit_center
  
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
### 📄 `tests/__init__.py`

```python

```
### 📄 `tests/conftest.py`

```python
import pytest
from celery_app import celery_app

@pytest.fixture(autouse=True, scope="session")
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield

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
### 📄 `tests/test_security.py`

```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from api.main import app
from config import logger
import time

client = TestClient(app)

def test_sql_injection_protection():
    """Проверка защиты от SQL injection"""
    # Попытка SQL injection в step
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": "api_latency_p99",
            "start": 1234567890,
            "end": 1234567900,
            "step": "1s; DROP TABLE canonical_metrics; --"
        }
    )
    assert response.status_code == 400
    assert "Invalid step" in response.json()["detail"]

def test_rate_limiting():
    """Проверка rate limiting"""
    rate_limit_hit = False
    
    # Отправляем запросы до срабатывания rate limit
    for i in range(20):
        response = client.post("/token", data={"username": "test", "password": "test"})
        if response.status_code == 429:
            rate_limit_hit = True
            break
        time.sleep(0.05)  # Небольшая задержка
    
    assert rate_limit_hit, "Rate limiting should have been triggered"
    
    # Проверяем, что после ожидания можно снова делать запросы
    time.sleep(60)  # Ждём сброс rate limit
    response = client.post("/token", data={"username": "test", "password": "test"})
    assert response.status_code in [200, 400, 401]

def test_metric_whitelist():
    """Проверка whitelist метрик"""
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": "malicious_metric",
            "start": 1234567890,
            "end": 1234567900,
            "step": "1m"
        }
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
def test_sql_injection_dimensions():
    """Тест защиты от SQL injection в dimensions"""
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": 'api_latency_p99{region="x";DROP TABLE--"}',
            "start": 1234567890,
            "end": 1234567900,
            "step": "1m"
        }
    )
    # Должен быть 400 Bad Request, а не 500 или 200
    assert response.status_code == 400
    assert "Invalid dimension key" in response.json()["detail"] or "forbidden characters" in response.text


def test_secret_masking_in_logs():
    """Убедимся, что секреты не попадают в логи"""
    import io
    from contextlib import redirect_stderr
    
    captured = io.StringIO()
    with redirect_stderr(captured):
        try:
            # Имитация ошибки подключения с паролем
            raise ConnectionError("redis://:super_secret_pass@localhost:6379")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
    
    log_output = captured.getvalue()
    assert "super_secret_pass" not in log_output
    assert "***" in log_output
```
### 📄 `tests/integration/test_end_to_end.py`

```python
# tests/integration/test_end_to_end.py
from fastapi.testclient import TestClient
from sqlalchemy import text
from api.main import app
from core.notifications import notify
from unittest.mock import patch
from core.database import get_engine

client = TestClient(app)

def test_webhook_to_db_to_api():
    # 1. Постим в webhook
    resp = client.post("/webhooks/grafana", json={
        "title": "Test",
        "message": "OK",
        "status": "firing"
    })
    assert resp.status_code == 200

    # 2. Ждём Celery (в тестах — вызываем напрямую)
    from tasks import run_alerts_check_task
    run_alerts_check_task() # type: ignore

    # 3. Проверяем, что запись появилась в canonical_metrics
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT metric_name, value FROM canonical_metrics
            WHERE metric_name = 'grafana_test' LIMIT 1
        """)).first()
        assert row is not None

    # 4. Проверяем API
    resp = client.post("/data/query", json={
        "metric_name": "grafana_test",
        "limit": 1
    })
    assert resp.status_code == 200
    assert len(resp.json()["points"]) > 0
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
from datetime import datetime, timedelta
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
HISTORY_KEY = "alert_history"
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

def is_alert_suppressed(alert_hash: str) -> bool:
    """Проверяет, подавлен ли алерт."""
    try:
        return get_cache().get(f"alert_suppression:{alert_hash}") is not None
    except Exception:
        return False


def are_alerts_suppressed(alert_hashes: list) -> dict:
    """Пакетная проверка подавления алертов."""
    if not alert_hashes:
        return {}
    
    cache = get_cache()
    keys = [f"alert_suppression:{h}" for h in alert_hashes]
    
    try:
        # Используем pipeline для одного запроса
        pipe = cache.pipeline()
        for key in keys:
            pipe.exists(key)
        results = pipe.execute()
        
        return {h: bool(r) for h, r in zip(alert_hashes, results)}
    except Exception:
        return {h: False for h in alert_hashes}

def suppress_alert(alert_hash: str, minutes: int):
    if alert_hash.startswith("escalation_"):
        return
    get_cache().setex(f"alert_suppression:{alert_hash}", minutes * 60, "1")

def track_escalation_data(metric: str, region: str, value: float):
    cache = get_cache()
    key = f"escalation_tracker:{metric}:{region}"
    hist = cache.get(key)
    hist = json.loads(hist) if hist else []
    hist.append({"timestamp": time.time(), "value": value})
    hist = hist[-10:]
    cache.setex(key, 3600, json.dumps(hist))

def is_steady_increase(vals: List[float]) -> bool:
    return len(vals) >= 3 and all(vals[i] > vals[i-1] for i in range(1, len(vals)))

def check_escalation_alert(metric: str, region: str, current_value: float, is_suppressed: bool) -> Optional[Tuple[str, str]]:
    if not is_suppressed:
        return None
    cache = get_cache()
    key = f"escalation_tracker:{metric}:{region}"
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

def create_incident_buffered(alert_message: str, metric: str, region: str, value: float, priority: str):
    data = {
        "alert_message": alert_message,
        "metric": metric,
        "region": region,
        "value": str(value),
        "priority": priority,
        "timestamp": datetime.utcnow()
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
        incident = Incident(**data, detected_at=data["timestamp"])
        s.add(incident)
        s.commit()
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
    t = threading.Thread(target=process_incident_buffer, daemon=True, name="IncidentProcessor")
    t.start()
    logger.info("✅ Процессор инцидентов запущен")

def get_alert_history() -> List[AlertLog]:
    try:
        raw = get_cache().get(HISTORY_KEY)
        if raw:
            return [AlertLog(**item) for item in json.loads(raw)]
    except Exception as e:
        logger.warning(f"Ошибка чтения истории: {e}")
    return []

def save_alert_history(history: List[AlertLog]):
    if len(history) > 100:
        history = history[-100:]
    try:
        data = [a.__dict__ for a in history]
        get_cache().setex(HISTORY_KEY, 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")

def check_for_alerts(df: pd.DataFrame, col: str, selected: str, last_alert_region: str, alert_settings: AlertSettings) -> Tuple[bool, str]:
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
    is_suppressed = is_alert_suppressed(alert_hash)

    escalation = check_escalation_alert(col, region, val, is_suppressed)
    if escalation:
        msg, prio = escalation
        notify(msg, prio)
        create_incident_buffered(msg, col, region, val, prio)
        track_escalation_data(col, region, val)
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
        existing = s.query(AlertEvent).filter_by(alert_hash=alert_hash).first()
        if existing and existing.sent_at and (
            datetime.utcnow() - existing.sent_at < timedelta(minutes=alert_settings.get_suppression_minutes(selected))
        ):
            suppress_alert(alert_hash, alert_settings.get_suppression_minutes(selected))
            return False, last_alert_region

        new_alert = AlertEvent(
            alert_hash=alert_hash,
            metric_name=selected,
            dimensions={"region": region},
            value=val,
            event_time=datetime.utcnow(),
            detected_at=datetime.utcnow(),
            status="firing",
            sent=False,
            fingerprint=alert_hash
        )
        s.add(new_alert)
        s.flush()

        # Отправка
        notify(msg, prio)
        new_alert.sent = True
        new_alert.sent_at = datetime.utcnow()

        # Инцидент
        create_incident_buffered(msg, selected, region, val, prio)
        new_alert.incident_created = True
        new_alert.incident_created_at = datetime.utcnow()

        s.commit()

        # История
        history = get_alert_history()
        history.append(AlertLog(time.time(), selected, region, val, prio))
        save_alert_history(history)

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

if __name__ != "__main__":
    start_incident_buffer_processor()
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


cache = get_cache()
CACHE_TTL = settings.cache_ttl

def create_mv():
    if not cache.exists("data_from_db_1h_zero"):
        logger.info("Создаем MV для данных из БД")
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_hourly_region_metrics;"))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW mv_hourly_region_metrics AS
                    SELECT
                    date_trunc('hour', timestamp AT TIME ZONE 'UTC') AS hour,
                    dimensions->>'region' AS region,
                    metric_name,
                    AVG(value) AS avg_value,
                    MAX(value) AS max_value,
                    COUNT(*) AS sample_count
                    FROM canonical_metrics
                    WHERE dimensions ? 'region'
                    GROUP BY 1, 2, 3;"""))

            conn.execute(text("""CREATE UNIQUE INDEX ON mv_hourly_region_metrics (hour, region, metric_name);"""))

def get_data_from_db(time_filter: str = "1h", fill_missing: str = "zero") -> pd.DataFrame:
    """Загружает данные из PostgreSQL с улучшенной обработкой ошибок"""
    key = f"data_from_db_{time_filter}_{fill_missing}"

    try:
        data = cache.get(key)
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

        cache.setex(key, CACHE_TTL, df_raw.to_json(orient="split"))
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
from typing import Callable
import logging
from threading import local
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("db")

# Глобальный engine
_engine_local = local()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OperationalError)
)
def get_engine():
    if not hasattr(_engine_local, "engine"):
        database_url = str(get_database_url())
        
        # Рассчитываем размер пула на основе нагрузки
        # Формула: (CPU cores * 2) + effective_spindle_count
        # Для 4 CPU + 1 диск = 9, округляем до 10-20
        pool_size = getattr(settings, "DB_POOL_SIZE", 20)
        max_overflow = getattr(settings, "DB_MAX_OVERFLOW", 40)
        
        _engine_local.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,  # Базовый размер пула
            max_overflow=max_overflow,  # Дополнительные соединения
            pool_timeout=30,  # Таймаут ожидания соединения
            pool_recycle=3600,  # Переиспользовать соединение каждый час
            pool_pre_ping=True,  # Проверка соединения перед использованием
            echo=False,
            connect_args={
                "options": "-c statement_timeout=30000",  # 30 секунд на запрос
                "connect_timeout": 10,  # Таймаут подключения
            }
        )
        
        with _engine_local.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info(f"✅ SQLAlchemy engine initialized (pool_size={pool_size}, max_overflow={max_overflow})")
    return _engine_local.engine
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
### 📄 `core/locking.py`

```python
# core/locking.py
import time
import logging
from contextlib import contextmanager
from config import settings, get_cache

logger = logging.getLogger(__name__)

cache = get_cache()

@contextmanager
def global_lock(lock_name: str, timeout: float = None): # type: ignore
    """
    Распределённая блокировка с использованием Redis (SETNX + EXPIRE)
    """
    if timeout is None:
        timeout = settings.cache_locking_timeout
    lock_key = f"lock_{lock_name}"
    cache = get_cache()
    acquired = False
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            # Пытаемся установить блокировку с TTL
            acquired = cache.set(lock_key, "1", nx=True, ex=int(timeout * 1.5))
            if acquired:
                break
            time.sleep(settings.cache_poll_interval)
        else:
            raise TimeoutError(f"Не удалось получить блокировку '{lock_name}' за {timeout} секунд")

        yield
    except Exception as e:
        if "yield" in str(e):  # Ошибка внутри yield
            raise
        else:
            logger.error(f"Ошибка в блокировке {lock_name}: {e}")
            raise
    finally:
        if acquired:
            try:
                # Удаляем блокировку только если она наша
                cache.delete(lock_key)
            except Exception as e:
                logger.error(f"Ошибка при освобождении блокировки {lock_key}: {e}")

def get_global_state(key: str, default=None):
    """Получить значение из глобального состояния"""
    return cache.get(f"global_state_{key}")

def set_global_state(key: str, value, expire=None):
    """Установить значение в глобальное состояние"""
    cache.set(f"global_state_{key}", value, ex=expire)
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
        self._cache = get_cache()
        self._logger = logger.getChild("metadata_service")

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

    def create_metric(self, dto: MetricDTO) -> str:
        with global_lock("metadata_metric_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_metrics (
                        metric_name, display_name, description, unit,
                        default_threshold, default_critical_threshold, is_active
                    ) VALUES (
                        :metric_name, :display_name, :description, :unit,
                        :default_threshold, :default_critical_threshold, :is_active
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
                with engine.begin() as conn:
                    result = conn.execute(query, asdict(dto))
                    metric_name = result.scalar_one()
                    self._invalidate_cache("metrics")
                    self._logger.info(f"✅ Метрика '{metric_name}' создана/обновлена")
                    return metric_name
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания метрики {dto.metric_name}: {mask_secrets(str(e))}")
                raise

    def get_metric(self, metric_name: str) -> Optional[MetricDTO]:
        key = f"metadata:metric:{metric_name}"
        cached = self._cache.get(key)
        if cached:
            return MetricDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_metrics WHERE metric_name = :name AND is_active = true")
            with engine.connect() as conn:
                row = conn.execute(query, {"name": metric_name}).mappings().first()
                if not row:
                    return None
                dto = MetricDTO(**row)
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"❌ Ошибка чтения метрики {metric_name}: {mask_secrets(str(e))}")
            return None

    def list_metrics(self, active_only: bool = True) -> List[MetricDTO]:
        key = "metadata:metrics:active" if active_only else "metadata:metrics:all"
        cached = self._cache.get(key)
        if cached:
            return [MetricDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            where = "WHERE is_active = true" if active_only else ""
            query = text(f"SELECT * FROM metadata_metrics {where} ORDER BY metric_name")
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = [MetricDTO(**row) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка метрик: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Dimensions ---

    def create_dimension(self, dto: DimensionDTO) -> str:
        with global_lock("metadata_dimension_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_dimensions (
                        dimension_key, description, allowed_values, is_required
                    ) VALUES (
                        :dimension_key, :description, :allowed_values, :is_required
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
                        "is_required": dto.is_required
                    })
                    dim_key = result.scalar_one()
                    self._invalidate_cache("dimensions")
                    self._logger.info(f"✅ Измерение '{dim_key}' создано/обновлено")
                    return dim_key
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания измерения {dto.dimension_key}: {mask_secrets(str(e))}")
                raise

    def get_dimension(self, dimension_key: str) -> Optional[DimensionDTO]:
        key = f"metadim:{dimension_key}"
        cached = self._cache.get(key)
        if cached:
            return DimensionDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_dimensions WHERE dimension_key = :key")
            with engine.connect() as conn:
                row = conn.execute(query, {"key": dimension_key}).mappings().first()
                if not row:
                    return None
                dto = DimensionDTO(**row)
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"❌ Ошибка чтения измерения {dimension_key}: {mask_secrets(str(e))}")
            return None

    def list_dimensions(self) -> List[DimensionDTO]:
        key = "metadimensions:all"
        cached = self._cache.get(key)
        if cached:
            return [DimensionDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_dimensions ORDER BY dimension_key")
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = [DimensionDTO(**row) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка измерений: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Rules ---

    def create_rule(self, dto: RuleDTO) -> uuid.UUID:
        rule_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_rule_{rule_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_rules (
                        id, name, description, condition, labels, actions, is_active
                    ) VALUES (
                        :id, :name, :description, :condition, :labels, :actions, :is_active
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
                        "is_active": dto.is_active
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("rules")
                    self._logger.info(f"✅ Правило '{dto.name}' (id={created_id}) создано/обновлено")
                    return created_id
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания правила {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_rules(self) -> List[RuleDTO]:
        key = "metadata:rules:active"
        cached = self._cache.get(key)
        if cached:
            return [RuleDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules
                WHERE is_active = true
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
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
            self._logger.error(f"❌ Ошибка списка правил: {mask_secrets(str(e))}")
            return []

    # --- CRUD: ML Configs ---

    def create_ml_config(self, dto: MLConfigDTO) -> uuid.UUID:
        config_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_ml_{config_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_ml_configs (
                        id, name, metric_name, group_by, methods, method_params,
                        retrain_schedule, auto_alert, alert_severity, is_active
                    ) VALUES (
                        :id, :name, :metric_name, :group_by, :methods, :method_params,
                        :retrain_schedule, :auto_alert, :alert_severity, :is_active
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
                        "is_active": dto.is_active
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("ml_configs")
                    self._logger.info(f"✅ ML-конфиг '{dto.name}' (id={created_id}) создан/обновлён")
                    return created_id
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания ML-конфига {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_ml_configs(self) -> List[MLConfigDTO]:
        key = "metadata:ml_configs:active"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                       retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                WHERE is_active = true
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
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
            self._logger.error(f"❌ Ошибка списка ML-конфигов: {mask_secrets(str(e))}")
            return []

    def list_all_ml_configs(self) -> List[MLConfigDTO]:
        # Аналогично list_active, но без WHERE is_active = true
        key = "metaml_configs:all"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                    retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
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
            self._logger.error(f"❌ Ошибка списка всех ML-конфигов: {mask_secrets(str(e))}")
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
import sys
import os
import torch
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
            group_by_keys = cfg.group_by or ["region"]  # по умолчанию — регион

            logger.info(f"Переобучение: {metric_name}, group_by={group_by_keys}")

            # Формируем условие для dimensions
            dimensions_filter = " AND ".join(
                f"dimensions->>'{key}' IS NOT NULL" for key in group_by_keys
            )

            query = f"""
            SELECT 
                timestamp,
                value,
                {", ".join(f"dimensions->>'{key}' as {key}" for key in group_by_keys)}
            FROM canonical_metrics
            WHERE metric_name = :metric_name
              AND timestamp >= :cutoff
              {f"AND {dimensions_filter}" if dimensions_filter else ""}
            ORDER BY timestamp
            LIMIT 10000
            """

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
class CanonicalMetric(Base):
    __tablename__ = "canonical_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    dimensions = Column(JSONB, nullable=False, default=dict)
    tags = Column(JSONB, nullable=False, default=dict)
    source = Column(String, nullable=True)

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
    status = Column(String, default="firing")  # firing, resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    fingerprint = Column(String, nullable=False, index=True)
    escalation_level = Column(Integer, default=0)
    last_escalation = Column(DateTime(timezone=True), nullable=True)
    alert_hash = Column(String, index=True)
    
    # 🔴 ДОБАВЛЕНО — критически недостающие поля:
    incident_created = Column(Boolean, default=False)
    incident_created_at = Column(DateTime(timezone=True), nullable=True)

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
    detected_at = Column(DateTime, default=datetime.utcnow)
    assigned_to = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
class MetadataMLConfig(Base):
    __tablename__ = "metadata_ml_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    metric_name = Column(String, ForeignKey("metadata_metrics.metric_name"), nullable=False)
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
