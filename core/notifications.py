# core/notifications.py
import signal
import sys
from config import logger, mask_secrets
from celery_app import celery_app
from tenacity import retry, stop_after_attempt, wait_fixed

class NotificationError(Exception):
    pass

# безопасно отправляем задачу без top-level импорта tasks
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def notify(message: str, priority: str = "info") -> None:
    try:
        celery_app.send_task("tasks.send_notification", args=[message, priority], kwargs={})
        logger.debug(f"📨 Уведомление отправлено в Celery: [{priority}] {message[:80]}...")
        try:
            from api.main import ALERTS_SENT
            ALERTS_SENT.labels(priority=priority).inc()
        except Exception:
            pass
    except Exception as e:
        logger.exception("❌ Ошибка при отправке уведомления в Celery")
        raise NotificationError(f"Failed to send notification: {mask_secrets(str(e))}")

# graceful shutdown handler — использует telegram helper (lazy import inside function)
def _shutdown_handler(signum, frame):
    logger.info(f"🛑 Получен сигнал {signal.strsignal(signum)} — graceful shutdown...")
    try:
        from telegram_bot import close_telegram_session_sync
        close_telegram_session_sync()
    except Exception:
        logger.debug("Не удалось закрыть Telegram session")
    logger.info("✅ Завершение работы.")
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT, _shutdown_handler)

logger.info("✅ Модуль уведомлений инициализирован")
