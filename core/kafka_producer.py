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
        _get_producer().send(TOPIC_ALERTS, value=data)
    except Exception as e:
        logger.error("Kafka publish_alert_event failed: %s", mask_secrets(str(e)))


def publish_metric_event(data: dict) -> None:
    try:
        _get_producer().send(TOPIC_METRICS, value=data)
    except Exception as e:
        logger.error("Kafka publish_metric_event failed: %s", mask_secrets(str(e)))
