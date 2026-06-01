# core/kafka_consumer.py
import json
from typing import List, Dict, Any
from kafka import KafkaConsumer
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine

TOPIC = "sit_center.metrics"
BATCH_SIZE = 100
POLL_TIMEOUT_MS = 1000


class MetricKafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str = "sit-center-ingest"):
        self.consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=False,
            max_poll_records=BATCH_SIZE,
        )
        self.engine = get_engine()
        logger.info("Kafka consumer initialized for topic: %s", TOPIC)

    def run(self):
        logger.info("Kafka consumer started")
        try:
            while True:
                self._poll_and_insert()
        except KeyboardInterrupt:
            logger.info("Kafka consumer shutting down")
        finally:
            self.consumer.close()

    def _poll_and_insert(self):
        messages = self.consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
        batch: List[Dict[str, Any]] = []

        for tp, records in messages.items():
            for record in records:
                msg = record.value
                batch.append({
                    "metric_name": msg["metric_name"],
                    "value": msg["value"],
                    "timestamp": msg.get("timestamp"),
                    "dimensions": json.dumps(msg.get("dimensions", {})),
                    "tags": json.dumps(msg.get("tags", {})),
                    "source": msg.get("source", "kafka"),
                })

                if len(batch) >= BATCH_SIZE:
                    self._bulk_insert(batch)
                    batch = []

        if batch:
            self._bulk_insert(batch)

        self.consumer.commit()

    def _bulk_insert(self, batch: List[Dict[str, Any]]):
        if not batch:
            return
        insert_sql = text("""
            INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source)
            VALUES (:metric_name, :value,
                    COALESCE(:timestamp::timestamptz, NOW()),
                    :dimensions::jsonb, :tags::jsonb, :source)
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(insert_sql, batch)
            logger.debug("Inserted %d metrics from Kafka", len(batch))
        except Exception as e:
            logger.error("Kafka bulk insert failed: %s", mask_secrets(str(e)))
