# Quick Start Guide

Minimal setup for local development (~2GB RAM). Full stack requires ~8GB RAM.

## Prerequisites

- Python 3.11–3.13 (NOT 3.14 — `tensorflow` has no 3.14 wheels yet)
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

This starts all 21 services. Requires ~8GB RAM.

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

**Database not found / tables missing**: The base schema is auto-created from `db/migrations/*.sql` on the **first** `docker compose up -d db` (fresh volume). Then run `alembic upgrade head` for the admin/ML-config tables. If you reused an old volume, the init scripts won't re-run — recreate it with `docker compose down -v`.

**ML tests fail**: ML tests require `prophet`, `tensorflow`, `torch` — skip with `--ignore=tests/test_ml.py`

**Rate limiting errors in tests**: Set `TESTING=1` environment variable
