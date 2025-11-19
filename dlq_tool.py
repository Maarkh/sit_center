# dlq_tool.py
from tasks import send_notification
from config import get_redis


def replay_dlq():
    r = get_redis()
    entries = r.xrange("dlq:notifications", count=10)
    for _id, fields in entries: # type: ignore
        # Если client был с decode_responses=True — поля уже str; иначе bytes
        def _get(field_name):
            v = fields.get(field_name)
            if isinstance(v, bytes):
                return v.decode()
            return v

        msg = _get("message") or ""
        priority = _get("priority") or "info"
        send_notification.delay(msg, priority) # type: ignore
        r.xdel("dlq:notifications", _id)
        print(f"🔁 Повтор: {msg[:80]}...")