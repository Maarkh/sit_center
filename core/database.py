# core/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from config import settings, get_database_url
import logging
import threading
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("db")

_engine = None
_engine_lock = threading.Lock()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OperationalError)
)
def get_engine():
    global _engine

    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        database_url = str(get_database_url())

        pool_size = getattr(settings, "DB_POOL_SIZE", 20)
        max_overflow = getattr(settings, "DB_MAX_OVERFLOW", 40)

        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "options": "-c statement_timeout=30000",
                "connect_timeout": 10,
            }
        )

        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info(f"SQLAlchemy engine initialized (pool_size={pool_size}, max_overflow={max_overflow})")

    return _engine
