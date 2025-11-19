# telegram_bot.py

import requests
from config import logger, settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.locking import global_lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Эмодзи для приоритетов
PRIORITY_EMOJI = {
    "info": "ℹ️",
    "warning": "🟡",
    "critical": "🔴",
    "error": "❌"
}

# Глобальная сессия (thread-safe)
_telegram_session = None


def get_session():
    global _telegram_session
    with global_lock("telegram_session"):
        if _telegram_session is None:
            _telegram_session = requests.Session()
            
            # Настройка retry на уровне сессии
            retry_strategy = Retry(
                total=3,  # Максимум 3 попытки
                backoff_factor=1,  # Экспоненциальная задержка
                status_forcelist=[429, 500, 502, 503, 504],  # Повтор на этих кодах
                allowed_methods=["POST"]  # Только POST
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            _telegram_session.mount("https://", adapter)
            _telegram_session.mount("http://", adapter)
            
            _telegram_session.headers.update({"User-Agent": "SituationalCenter/1.0"})
            logger.debug("Создана новая requests.Session для Telegram с retry")
        
        return _telegram_session

def close_telegram_session_sync():
    global _telegram_session
    with global_lock("telegram_session_close"):
        try:
            if _telegram_session is not None:
                # у requests.Session есть метод close()
                close_fn = getattr(_telegram_session, "close", None)
                if callable(close_fn):
                    close_fn()
                _telegram_session = None
                logger.info("✅ Telegram session закрыта")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии Telegram session: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((
        requests.Timeout,
        requests.ConnectionError,
        requests.HTTPError
    )),
    reraise=False,  # Не поднимаем исключение после всех попыток
    before_sleep=lambda retry_state: logger.warning(
        f"Повторная попытка отправки уведомления ({retry_state.attempt_number}/3)..."
    ),
    after=lambda retry_state: logger.error(
        f"Не удалось отправить уведомление после {retry_state.attempt_number} попыток"
    ) if retry_state.outcome.failed else None # type: ignore
)
def send_alert_sync(message: str, priority: str = "info") -> bool:
    """
    Синхронная отправка уведомления в Telegram с retry и таймаутами.
    
    Returns:
        bool: True если отправлено успешно, False иначе
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не задан")
        return False
    
    # Выбор чата по приоритету
    chat_id = settings.TELEGRAM_CHAT_ID
    if priority == "critical":
        chat_id = settings.TELEGRAM_CHAT_ID_CRITICAL or chat_id
    elif priority == "warning":
        chat_id = settings.TELEGRAM_CHAT_ID_WARNING or chat_id
    
    if not chat_id:
        logger.error(f"ID чата не определён для приоритета {priority}")
        return False

    emoji = PRIORITY_EMOJI.get(priority, "ℹ️")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"{emoji} {message}",
        "parse_mode": "HTML",
        "disable_notification": priority == "info",
    }

    session = get_session()
    try:
        # Таймауты: (connect, read)
        resp = session.post(url, json=payload, timeout=(5, 10))
        resp.raise_for_status()
        
        result = resp.json()
        if result.get("ok"):
            logger.info(f"✅ Telegram: {message[:50]}...")
            return True
        else:
            err = result.get("description", "неизвестная ошибка API")
            logger.error(f"❌ Telegram API: {err}")
            return False
    
    except requests.Timeout:
        logger.error(f"⏰ Таймаут при отправке в Telegram ({url})")
        raise  # Retry сработает
    
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        if status_code == 429:
            logger.warning("🚦 Telegram Rate Limit — ждем...")
            raise  # Retry с backoff
        elif status_code and 500 <= status_code < 600:
            logger.error(f"🔥 Telegram server error: {status_code}")
            raise  # Retry
        else:
            logger.error(f"❌ Telegram HTTP error: {e}")
            return False  # Не ретраим
    
    except requests.ConnectionError as e:
        logger.error(f"📡 Ошибка подключения к Telegram: {e}")
        raise  # Retry
    
    except Exception as e:
        logger.exception(f"💥 Неожиданная ошибка при отправке в Telegram: {e}")
        return False