# core/locking.py
import time
import logging
from contextlib import contextmanager
from config import settings, get_cache

logger = logging.getLogger(__name__)

cache = get_cache()

@contextmanager
def global_lock(lock_name: str, timeout: float = None): # type: ignore
    """
    Распределённая блокировка с использованием Redis (SETNX + EXPIRE)
    """
    if timeout is None:
        timeout = settings.cache_locking_timeout
    lock_key = f"lock_{lock_name}"
    cache = get_cache()
    acquired = False
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            # Пытаемся установить блокировку с TTL
            acquired = cache.set(lock_key, "1", nx=True, ex=int(timeout * 1.5))
            if acquired:
                break
            time.sleep(settings.cache_poll_interval)
        else:
            raise TimeoutError(f"Не удалось получить блокировку '{lock_name}' за {timeout} секунд")

        yield
    except Exception as e:
        if "yield" in str(e):  # Ошибка внутри yield
            raise
        else:
            logger.error(f"Ошибка в блокировке {lock_name}: {e}")
            raise
    finally:
        if acquired:
            try:
                # Удаляем блокировку только если она наша
                cache.delete(lock_key)
            except Exception as e:
                logger.error(f"Ошибка при освобождении блокировки {lock_key}: {e}")

def get_global_state(key: str, default=None):
    """Получить значение из глобального состояния"""
    return cache.get(f"global_state_{key}")

def set_global_state(key: str, value, expire=None):
    """Установить значение в глобальное состояние"""
    cache.set(f"global_state_{key}", value, ex=expire)