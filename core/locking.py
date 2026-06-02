# core/locking.py
import time
import uuid
import logging
import threading
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

# Lua-скрипт: продлить TTL только если ключ всё ещё наш (lease renewal).
_EXTEND_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("pexpire", KEYS[1], ARGV[2])
else
    return 0
end
"""

@contextmanager
def global_lock(lock_name: str, timeout: float = None):  # type: ignore
    """
    Распределённая блокировка через Redis (SETNX + PEXPIRE).
    Безопасное освобождение через Lua-скрипт (проверка owner).

    Lease renewal (watchdog): пока критическая секция выполняется, фоновый поток
    периодически продлевает TTL ключа. Это убирает класс багов «секция работает
    дольше TTL → ключ истёк → два держателя одновременно». TTL продлевается только
    если ключ всё ещё наш (CAS через Lua).
    """
    if timeout is None:
        timeout = settings.cache_locking_timeout
    lock_key = f"lock_{lock_name}"
    lock_value = str(uuid.uuid4())
    cache = get_cache()
    acquired = False
    start_time = time.time()
    ttl_ms = max(int(timeout * 1.5 * 1000), 1000)
    stop_renew = threading.Event()
    renew_thread = None

    try:
        while time.time() - start_time < timeout:
            acquired = cache.set(lock_key, lock_value, nx=True, px=ttl_ms)
            if acquired:
                break
            time.sleep(settings.cache_poll_interval)
        else:
            raise TimeoutError(f"Failed to acquire lock '{lock_name}' within {timeout}s")

        # Watchdog: продлеваем lease на ~1/3 TTL, пока удерживаем блокировку.
        def _renew():
            interval = max(ttl_ms / 1000.0 / 3.0, 1.0)
            while not stop_renew.wait(interval):
                try:
                    ok = cache.eval(_EXTEND_SCRIPT, 1, lock_key, lock_value, ttl_ms)
                    if not ok:
                        # Ключ уже не наш (истёк/перехвачен) — продлевать нечего.
                        logger.warning(f"Lock {lock_key} lost before renewal; stopping watchdog")
                        break
                except Exception as e:
                    logger.warning(f"Lock renew failed for {lock_key}: {e}")
                    break

        renew_thread = threading.Thread(target=_renew, name=f"lock-renew-{lock_name}", daemon=True)
        renew_thread.start()

        yield
    finally:
        stop_renew.set()
        if renew_thread is not None:
            renew_thread.join(timeout=1)
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
