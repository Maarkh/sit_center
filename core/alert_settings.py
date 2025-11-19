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
    
