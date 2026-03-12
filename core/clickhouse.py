# core/clickhouse.py
import threading
from config import settings, logger, mask_secrets

_client = None
_lock = threading.Lock()


def get_clickhouse_client():
    global _client
    if _client is not None:
        return _client

    with _lock:
        if _client is not None:
            return _client

        import clickhouse_connect

        host = getattr(settings, "CLICKHOUSE_HOST", "clickhouse")
        port = int(getattr(settings, "CLICKHOUSE_PORT", 8123))
        user = getattr(settings, "CLICKHOUSE_USER", "default")
        password = getattr(settings, "CLICKHOUSE_PASSWORD", "")
        database = getattr(settings, "CLICKHOUSE_DB", "sit_center")

        try:
            _client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=user,
                password=password,
                database=database,
            )
            logger.info("ClickHouse client initialized (%s:%s/%s)", host, port, database)
        except Exception as e:
            logger.error("Failed to connect to ClickHouse: %s", mask_secrets(str(e)))
            raise

    return _client
