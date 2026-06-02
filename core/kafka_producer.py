# core/kafka_producer.py
import json
from kafka import KafkaProducer
from config import settings, logger, mask_secrets

_producer = None

TOPIC_ALERTS = "sit_center.alerts"
TOPIC_METRICS = "sit_center.metrics"


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode("utf-8"),
            acks="all",
            retries=3,
        )
    return _producer


def publish_alert_event(data: dict) -> None:
    try:
        producer = _get_producer()
        future = producer.send(TOPIC_ALERTS, value=data)
        future.add_errback(
            lambda e: logger.error("Kafka alert delivery failed: %s", mask_secrets(str(e)))
        )
        # Alerts are low-volume and important: block briefly so a broker error
        # surfaces here instead of being silently swallowed by fire-and-forget.
        producer.flush(timeout=5)
    except Exception as e:
        logger.error("Kafka publish_alert_event failed: %s", mask_secrets(str(e)))


def publish_metric_event(data: dict) -> None:
    try:
        future = _get_producer().send(TOPIC_METRICS, value=data)
        # High-volume path: don't block on flush, but still surface async
        # delivery errors instead of dropping them silently.
        future.add_errback(
            lambda e: logger.error("Kafka metric delivery failed: %s", mask_secrets(str(e)))
        )
    except Exception as e:
        logger.error("Kafka publish_metric_event failed: %s", mask_secrets(str(e)))
