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
            # earliest: on a fresh group, replay the backlog rather than silently
            # skipping everything produced before the consumer first connected.
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=BATCH_SIZE,
        )
        self.engine = get_engine()
        logger.info("Kafka consumer initialized for topic: %s", TOPIC)

    def run(self):
        logger.info("Kafka consumer started")
        try:
            while True:
                try:
                    self._poll_and_insert()
                except Exception as e:
                    # Insert failed → offsets were NOT committed. Rewind the
                    # in-memory position back to the last committed offset so the
                    # same records are re-delivered on the next poll instead of
                    # being silently skipped (at-least-once delivery).
                    logger.error(
                        "Kafka poll/insert cycle failed, rewinding to committed offsets: %s",
                        mask_secrets(str(e)),
                    )
                    self._seek_to_committed()
        except KeyboardInterrupt:
            logger.info("Kafka consumer shutting down")
        finally:
            self.consumer.close()

    def _poll_and_insert(self):
        messages = self.consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
        if not messages:
            return

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

        if batch:
            # Raises on failure → commit below is skipped → at-least-once.
            self._bulk_insert(batch)

        # Only advance committed offsets after the batch is durably persisted.
        self.consumer.commit()

    def _seek_to_committed(self):
        """Rewind every assigned partition to its last committed offset."""
        for tp in self.consumer.assignment():
            committed = self.consumer.committed(tp)
            if committed is not None:
                self.consumer.seek(tp, committed)
            else:
                self.consumer.seek_to_beginning(tp)

    def _bulk_insert(self, batch: List[Dict[str, Any]]):
        if not batch:
            return
        insert_sql = text("""
            INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source)
            VALUES (:metric_name, :value,
                    COALESCE(:timestamp::timestamptz, NOW()),
                    :dimensions::jsonb, :tags::jsonb, :source)
        """)
        # Let exceptions propagate: the caller relies on a raised error to skip
        # the offset commit. Swallowing here would commit offsets for data that
        # was never written, permanently losing the batch.
        with self.engine.begin() as conn:
            conn.execute(insert_sql, batch)
        logger.debug("Inserted %d metrics from Kafka", len(batch))
