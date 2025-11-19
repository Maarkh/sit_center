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