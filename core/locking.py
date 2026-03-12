# core/locking.py
import time
import uuid
import logging
from contextlib import contextmanager
from config import settings, get_cache

logger = logging.getLogger(__name__)

# Lua-скрипт: удалить ключ только если значение совпадает (наша блокировка)
_UNLOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

@contextmanager
def global_lock(lock_name: str, timeout: float = None):  # type: ignore
    """
    Распределённая блокировка с использованием Redis (SETNX + EXPIRE).
    Безопасное освобождение через Lua-скрипт (проверка owner).
    """
    if timeout is None:
        timeout = settings.cache_locking_timeout
    lock_key = f"lock_{lock_name}"
    lock_value = str(uuid.uuid4())
    cache = get_cache()
    acquired = False
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            acquired = cache.set(lock_key, lock_value, nx=True, ex=int(timeout * 1.5))
            if acquired:
                break
            time.sleep(settings.cache_poll_interval)
        else:
            raise TimeoutError(f"Failed to acquire lock '{lock_name}' within {timeout}s")

        yield
    finally:
        if acquired:
            try:
                cache.eval(_UNLOCK_SCRIPT, 1, lock_key, lock_value)
            except Exception as e:
                logger.error(f"Error releasing lock {lock_key}: {e}")


def get_global_state(key: str, default=None):
    """Get value from global state"""
    return get_cache().get(f"global_state_{key}")


def set_global_state(key: str, value, expire=None):
    """Set value in global state"""
    get_cache().set(f"global_state_{key}", value, ex=expire)
