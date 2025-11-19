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