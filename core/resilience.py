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
    Logs to sync_log and enqueues for retry via Celery."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"i-doit push failed in {func.__name__}: {e}. Will retry via Celery.")
            try:
                from celery_app import celery_app
                celery_app.send_task(
                    "tasks.retry_idoit_push",
                    args=[func.__name__, args, kwargs],
                    countdown=60,
                )
            except Exception as retry_err:
                logger.error(f"Failed to enqueue i-doit retry: {retry_err}")
            return None
    return wrapper
