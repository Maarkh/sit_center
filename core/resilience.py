# core/resilience.py
"""Graceful degradation helpers: Redis fallback, i-doit retry queue."""
import functools
from config import logger


def redis_fallback(default=None):
    """Decorator: if Redis is unavailable, return default instead of crashing."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Redis unavailable in {func.__name__}, returning fallback: {e}")
                return default() if callable(default) else default
        return wrapper
    return decorator


def safe_idoit_push(func):
    """Decorator: swallow i-doit push errors so they never crash callers.

    The failed push is logged (and the i-doit sync flow records its own sync_log row)
    so it can be replayed. NB: this used to `send_task("tasks.retry_idoit_push", ...)`
    with the original args/kwargs — but no such task exists, and a generic
    re-invoke-by-name with arbitrary (often non-JSON-serializable) args could never
    work over Celery's json serializer. That broken enqueue is removed; a real retry
    needs a durable job carrying the actual push payload, not a function re-invoke."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("i-doit push failed in %s: %s (swallowed; see sync_log to replay)",
                         func.__name__, e)
            return None
    return wrapper
