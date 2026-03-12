# kafka_consumer_main.py
"""Entry point for the Kafka consumer service."""
from config import settings, logger

if __name__ == "__main__":
    bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    logger.info("Starting Kafka consumer with bootstrap: %s", bootstrap)

    from core.kafka_consumer import MetricKafkaConsumer
    consumer = MetricKafkaConsumer(bootstrap_servers=bootstrap)
    consumer.run()
