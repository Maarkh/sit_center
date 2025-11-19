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