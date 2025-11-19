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