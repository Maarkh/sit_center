# core/pubsub.py
import json
import redis
import redis.asyncio as aioredis
from config import settings, logger, mask_secrets

ALERT_CHANNEL = "sit_center:alerts"


def _get_redis_url() -> str:
    if settings.REDIS_URL:
        return settings.REDIS_URL
    pwd = settings.REDIS_PASSWORD or ""
    return f"redis://:{pwd}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


def publish_alert(data: dict) -> None:
    """Publish an alert to Redis Pub/Sub (sync, for Celery/alerts)."""
    try:
        r = redis.from_url(_get_redis_url(), decode_responses=True)
        r.publish(ALERT_CHANNEL, json.dumps(data, ensure_ascii=False, default=str))
        r.close()
    except Exception as e:
        logger.error(f"Failed to publish alert: {mask_secrets(str(e))}")


async def subscribe_alerts(callback):
    """Subscribe to alert channel and invoke callback for each message (async, for WS)."""
    while True:
        r = pubsub = None  # bind before try so the finally never hits an unbound name
        try:
            r = aioredis.from_url(_get_redis_url(), decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(ALERT_CHANNEL)
            logger.info("Subscribed to Redis Pub/Sub channel: %s", ALERT_CHANNEL)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await callback(data)
                    except Exception as e:
                        logger.warning(f"Error processing pubsub message: {e}")

        except Exception as e:
            logger.error(f"Redis Pub/Sub connection error: {mask_secrets(str(e))}")
            import asyncio
            await asyncio.sleep(5)
        finally:
            try:
                if pubsub is not None:
                    await pubsub.unsubscribe(ALERT_CHANNEL)
                if r is not None:
                    await r.aclose()
            except Exception:
                pass
