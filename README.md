# 📄 Ситуационный центр — СППР

## 📝 Описание

**Система поддержки принятия решений (СППР / DSS)** для региональных показателей
(сеть, логистика, ИТ, ИБ, жалобы). Это не просто мониторинг: система ведёт оператора
по полному циклу принятия решения — **Observe → Orient → Project → Decide → Act → Learn** —
от показателей с целевым коридором до исполняемого регламента и обучения на исходах.

> Подробное руководство «как работать» — **[docs/dss-guide.md](docs/dss-guide.md)**.
> Целевая архитектура — [DSS_TARGET_ARCHITECTURE.md](DSS_TARGET_ARCHITECTURE.md).

## 🧭 Возможности

- **Показатели и цели** с двусторонним целевым коридором, факторами и подписками (M2).
- **Отклонения и «хроника»** — детекция выхода за коридор и устойчивости (M3).
- **Ситуации** — корреляция связанных отклонений, оценка влияния, гипотеза первопричины (M4).
- **Предиктивные алерты** — прогноз выйдет за коридор → упреждение до пробоя (M5).
- **Рекомендации (Next-Best-Action)** — playbook'и, ранжирование, запуск регламента (M7).
- **Процессы/регламенты** — шаги, чек-листы, отчёты, эскалация по SLA (M8).
- **Журнал решений и обучение** — исход решения + win-rate playbook'ов обратно в скоринг (M10).
- **What-if** — сценарное моделирование и оценка потенциала (M6).
- **Кокпит** — React-интерфейс с деревом-светофором, ситуациями, графиками прогноза,
  таймлайном процессов, журналом решений и песочницей what-if (M11).
- Базовый мониторинг: интерактивная карта, метрики, алерты, инциденты, уведомления.
- Мультитенантность, RBAC, аудит, наблюдаемость (Prometheus/OTel), CI/CD.

## 🏗️ Стек

FastAPI · SQLAlchemy 2.0 · TimescaleDB · Redis · Celery · (опц. Kafka, ClickHouse) ·
React 19 + TypeScript + Ant Design 6 + Vite + ECharts.

## ▶️ Запуск (локально для теста)

```bash
# 1. Инфраструктура (TimescaleDB + Redis). Миграции из db/migrations/*.sql
#    применяются автоматически при первом старте (свежий volume).
docker compose -f docker-compose.test.yml up -d test-db test-redis

# 2. Backend (env указывает на тестовую БД; пароль admin — bcrypt-хэш ниже)
export DATABASE_URL=postgresql://test_user:test_pass@localhost:5444/test_db
export REDIS_HOST=localhost REDIS_PORT=6399 REDIS_PASSWORD=""
export SECRET_KEY=dev-secret ADMIN_USERNAME=admin COOKIE_SECURE=false
export ADMIN_PASSWORD='$2b$12$og87/j8zmULE7nd6EUpud.rS/8xpxmW5GaciRZBG.hkHQztviVeri'
.venv/bin/python -m uvicorn api.main:app --port 8000

# 3. (опц.) демо-данные для кокпита — в отдельном терминале, тот же env + PYTHONPATH=.
PYTHONPATH=. .venv/bin/python scripts/seed_demo.py

# 4. Frontend
cd frontend && npx vite --port 3010
```

- Кокпит: **http://localhost:3010** (логин `admin` / `admin`)
- API-документация (Swagger): **http://localhost:8000/docs**

### Продакшен

```bash
docker compose -f docker-compose.prod.yml up -d
```

См. [QUICKSTART.md](QUICKSTART.md) для полного стека (Celery, ML-воркер, Kafka, ClickHouse,
Grafana, Keycloak, i-doit) и [docs/operations.md](docs/operations.md) для эксплуатации.

## 🧪 Тестирование

```bash
# Backend — unit (мокнутая БД)
LOG_FORMAT=text TESTING=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_ml.py --ignore=tests/integration

# Backend — integration (реальная TimescaleDB; стек из шага 1 + env)
.venv/bin/python -m pytest tests/integration/ -v

# Frontend
cd frontend && npx vitest run        # unit
cd frontend && npx playwright test   # e2e
```

CI (`.github/workflows/ci-cd.yml`): lint · security (pip-audit + bandit) · unit ·
**integration** (накат всех миграций на реальную TimescaleDB + проверка схемы) · build.

## 📚 Документация

- **[docs/dss-guide.md](docs/dss-guide.md)** — как работает СППР, кокпит, API, сценарий end-to-end.
- [DSS_TARGET_ARCHITECTURE.md](DSS_TARGET_ARCHITECTURE.md) — целевая архитектура (12 модулей, статус).
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура (C4, ER, эндпоинты).
- [docs/operations.md](docs/operations.md) — эксплуатация, мониторинг, секреты, фоновые задачи.
- [docs/disaster-recovery.md](docs/disaster-recovery.md) — RTO/RPO, бэкапы.
- [docs/adr/](docs/adr/) — архитектурные решения (ADR).

## 📁 Структура проекта

```
api/            — FastAPI: роуты (вкл. DSS), middleware, auth, схемы (schemas_dss.py)
core/           — бизнес-логика + DSS-движки (*_engine.py), Celery-задачи (dss_tasks.py)
db/migrations/  — SQL-миграции (источник истины схемы; 010–017 — модули DSS)
frontend/       — React 19 + TS + Ant Design 6 + Vite (кокпит: src/pages/Cockpit/*)
scripts/        — служебные скрипты (seed_demo.py — демо-данные кокпита)
tests/          — pytest (unit, integration), Vitest/Playwright во frontend/
k8s/            — Helm-чарт · grafana/ — дашборды · docs/ — документация и ADR
```
