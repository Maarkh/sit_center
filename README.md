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
5. Создайте файл `.env` на основе `env.example` и заполните его.
6. Создайте базу данных и сгенерируйте данные: `python generate_data.py --init-db --fill-sample --init-metadata`
   (без флагов скрипт ничего не делает; при запуске БД через `docker compose` базовая схема создаётся автоматически из `db/migrations/`, и достаточно `--fill-sample --init-metadata`).

## ▶️ Запуск

### Локальная разработка

```bash
# 1. Поднять PostgreSQL + Redis
docker compose -f docker-compose.prod.yml up -d db redis

# 2. Применить миграции
alembic upgrade head

# 3. Запустить API-сервер
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API-документация будет доступна на `http://localhost:8000/docs`.

### Продакшен

```bash
docker compose -f docker-compose.prod.yml up -d
```

См. [QUICKSTART.md](QUICKSTART.md) для подробной инструкции по запуску всего стека.

## 🧪 Тестирование

```bash
# Backend
LOG_FORMAT=text TESTING=1 python -m pytest tests/ --ignore=tests/test_ml.py

# Frontend
cd frontend && npx vitest run        # unit
cd frontend && npx playwright test   # e2e
```

## 📚 Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура (C4, ER-диаграмма, эндпоинты).
- [docs/operations.md](docs/operations.md) — эксплуатация, мониторинг, ротация секретов.
- [docs/disaster-recovery.md](docs/disaster-recovery.md) — RTO/RPO, бэкапы.
- [docs/adr/](docs/adr/) — архитектурные решения (ADR).

## 📁 Структура проекта

> Полное дерево структуры генерируется автоматически: `python generate_docs.py`
> (README остаётся лёгким; полный листинг кода сохраняется в `.docx` в `documents/`).

```
api/        — FastAPI: роуты, middleware, auth, схемы
core/       — бизнес-логика: метрики, алерты, правила, ML, интеграции (i-doit, Kafka, Vault)
frontend/   — React 19 + TypeScript + Ant Design 6 + Vite
tests/      — pytest (unit, integration, load)
k8s/        — Helm-чарт
grafana/    — дашборды
docs/       — документация и ADR
alembic/    — миграции БД
```
