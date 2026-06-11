# core/kafka_consumer.py
import json
from typing import List, Dict, Any
from kafka import KafkaConsumer
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine
from core.data_sources import resolve_kafka_topics, resolve_kafka_bootstrap

TOPIC = "sit_center.metrics"
BATCH_SIZE = 100
POLL_TIMEOUT_MS = 1000


class MetricKafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str = "sit-center-ingest",
                 tenant_id: str = "default"):
        # Topics + bootstrap come from the data-source registry (enabled kafka sources)
        # with the env values as fallback — so adding a kafka source in the admin UI
        # subscribes the consumer to its topic/cluster on the next restart.
        self.tenant_id = tenant_id
        self.topics = resolve_kafka_topics(TOPIC, tenant_id) or [TOPIC]
        bootstrap = resolve_kafka_bootstrap(bootstrap_servers, tenant_id) or bootstrap_servers
        self.consumer = KafkaConsumer(
            *self.topics,
            bootstrap_servers=bootstrap,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            # earliest: on a fresh group, replay the backlog rather than silently
            # skipping everything produced before the consumer first connected.
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=BATCH_SIZE,
        )
        self.engine = get_engine()
        logger.info("Kafka consumer initialized for topics: %s", self.topics)

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
        skipped = 0
        for tp, records in messages.items():
            for record in records:
                msg = record.value
                try:
                    # Build defensively: a missing key / non-numeric value must NOT wedge
                    # the partition. Without this, one malformed record raises → offsets
                    # aren't committed → the same poison pill re-delivers forever.
                    row = {
                        "metric_name": str(msg["metric_name"]),
                        "value": float(msg["value"]),
                        "timestamp": msg.get("timestamp"),
                        "dimensions": json.dumps(msg.get("dimensions", {})),
                        "tags": json.dumps(msg.get("tags", {})),
                        "source": msg.get("source", "kafka"),
                        # tenant from the message, else this consumer's tenant (NOT the DDL
                        # default) — otherwise all streamed metrics land in 'default'.
                        "tenant_id": msg.get("tenant_id") or self.tenant_id,
                    }
                except (KeyError, TypeError, ValueError) as e:
                    skipped += 1
                    logger.warning("Kafka: skipping malformed metric record: %s", mask_secrets(str(e)))
                    continue
                batch.append(row)

        if skipped:
            logger.warning("Kafka: skipped %d malformed record(s) this batch", skipped)

        if batch:
            # Raises only on a DB/infra failure (transient) → commit below is skipped →
            # at-least-once retry. Malformed records were already filtered out above.
            self._bulk_insert(batch)

        # Advance committed offsets past the whole poll (good + skipped-bad) so a single
        # poison-pill record can't permanently stall the partition's ingestion.
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
        # CAST(... AS ...) not '::' — SQLAlchemy text() mis-parses a bind param
        # immediately followed by '::', producing a psycopg2 syntax error.
        insert_sql = text("""
            INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id)
            VALUES (:metric_name, :value,
                    COALESCE(CAST(:timestamp AS timestamptz), NOW()),
                    CAST(:dimensions AS jsonb), CAST(:tags AS jsonb), :source, :tenant_id)
        """)
        # Let exceptions propagate: the caller relies on a raised error to skip
        # the offset commit. Swallowing here would commit offsets for data that
        # was never written, permanently losing the batch.
        with self.engine.begin() as conn:
            conn.execute(insert_sql, batch)
        logger.debug("Inserted %d metrics from Kafka", len(batch))
