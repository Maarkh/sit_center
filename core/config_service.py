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