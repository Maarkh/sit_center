# core/notifications.py
from config import logger, mask_secrets
from celery_app import celery_app
from tenacity import retry, stop_after_attempt, wait_fixed

class NotificationError(Exception):
    pass

# безопасно отправляем задачу без top-level импорта tasks
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def notify(message: str, priority: str = "info", event_type: str = "system") -> None:
    try:
        celery_app.send_task("tasks.send_notification", args=[message, priority],
                             kwargs={"event_type": event_type})
        logger.debug(f"📨 Уведомление отправлено в Celery: [{priority}/{event_type}] {message[:80]}...")
        try:
            from api.main import ALERTS_SENT
            ALERTS_SENT.labels(priority=priority).inc()
        except Exception:
            pass
    except Exception as e:
        logger.exception("❌ Ошибка при отправке уведомления в Celery")
        raise NotificationError(f"Failed to send notification: {mask_secrets(str(e))}")

# NB: this module is imported by tasks.py (the Celery worker/beat entrypoint), so it
# must NOT install process-wide signal handlers at import — doing so overrode Celery's
# own SIGTERM graceful-drain with a bare sys.exit(0), requeuing in-flight tasks and
# orphaning locks. Telegram-session cleanup now runs from Celery's worker_shutting_down
# signal (celery_app.py) and the FastAPI lifespan, in the process that actually owns it.
logger.info("✅ Модуль уведомлений инициализирован")
