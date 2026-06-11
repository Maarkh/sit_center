# core/metric_service.py
from typing import List, Optional
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


def load_metrics_from_db(force_refresh: bool = False, tenant_id: str = "default") -> List[Metric]:
    """Load active metrics from the canonical catalog (`metadata_metrics`) — the table
    the admin Metric-catalog UI (M1) manages. Previously this read a legacy `metrics`
    table via ConfigService, but that table is not in the schema, so alerts/ML saw
    nothing and metrics created in the UI were invisible to the engines. Maps
    metric_name→column, default_threshold→threshold; priority/weight are unused by any
    consumer and default to 1.
    """
    from sqlalchemy import text
    from core.database import get_engine

    try:
        with get_engine().connect() as conn:
            rows = conn.execute(
                text("SELECT metric_name, display_name, default_threshold "
                     "FROM metadata_metrics WHERE is_active = true AND tenant_id = :tid "
                     "ORDER BY metric_name"),
                {"tid": tenant_id},
            ).mappings().all()

        metrics = [
            Metric(
                column=r["metric_name"],
                display_name=r["display_name"],
                threshold=int(r["default_threshold"]) if r["default_threshold"] is not None else 0,
                priority=1,
                weight=1.0,
                is_active=True,
            )
            for r in rows
        ]
        logger.info(f"✅ Загружено {len(metrics)} активных метрик из metadata_metrics")
        return metrics

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки метрик из metadata_metrics: {mask_secrets(str(e))}")
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
            logger.info(f"✅ Загружено {len(metrics)} активных метрик из metadata_metrics (cached)")
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик в кэш: {mask_secrets(str(e))}")

        return metrics

def get_metric_by_column(col: str) -> Optional[Metric]:
    metrics = load_metrics_from_db_cached()
    return next((m for m in metrics if m.column == col), None)

