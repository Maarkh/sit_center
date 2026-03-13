# ADR-004: Kafka as Optional Ingestion Layer

## Status

Accepted

## Date

2025-11-20

## Context

The Sit Center ingests metrics from monitored infrastructure via a REST API. For low-to-medium throughput scenarios (hundreds of metrics per second), the direct REST-to-database path works well: the API validates incoming data and inserts it into TimescaleDB.

However, some deployment environments have high-frequency metric sources (thousands of metrics per second) that create problems with direct ingestion:

- **Burst handling**: Sudden spikes in metric volume can overwhelm the API and saturate database connections.
- **Backpressure**: The REST API has no built-in buffering. If the database is slow (e.g., during compression or maintenance), ingestion requests fail or time out.
- **Producer coupling**: Metric producers must handle HTTP errors and retries, adding complexity to monitoring agents.
- **Batch efficiency**: Individual REST calls insert one or a few metrics at a time. Batch inserts into TimescaleDB are significantly more efficient.

Not all deployments need high-throughput ingestion. Smaller installations should not be forced to operate Kafka infrastructure.

## Decision

Introduce Kafka as an optional ingestion layer, controlled by the `KAFKA_ENABLED` configuration flag.

When Kafka is enabled:

1. Metric producers publish to a Kafka topic instead of (or in addition to) the REST API.
2. A dedicated Kafka consumer service reads from the topic and performs batch inserts into TimescaleDB.
3. Consumer offsets provide at-least-once delivery semantics. Failed batches are retried from the last committed offset.
4. The consumer uses configurable batch sizes and flush intervals to optimize insert performance.

When Kafka is disabled:

1. The REST API remains the sole ingestion path.
2. No Kafka infrastructure is required.
3. The Kafka consumer service is not started.

The health endpoint (`/health`) checks Kafka connectivity only when `KAFKA_ENABLED=true`. When disabled, Kafka health is not evaluated.

## Consequences

### Positive

- **Burst buffering**: Kafka absorbs traffic spikes, allowing the consumer to process at a sustainable rate regardless of producer throughput.
- **Reliable delivery**: Consumer offset tracking ensures no metrics are lost even if the consumer or database is temporarily unavailable.
- **Decoupled producers**: Metric sources publish to Kafka and move on. They do not need to handle database availability or API errors.
- **Batch efficiency**: The consumer accumulates metrics and performs batch inserts, which are significantly faster than individual REST API calls for TimescaleDB.
- **Optional deployment**: Smaller installations avoid Kafka complexity entirely by leaving `KAFKA_ENABLED=false`.

### Negative

- **Operational complexity**: Kafka requires Zookeeper (or KRaft), brokers, topic management, and monitoring. This is significant infrastructure overhead for deployments that enable it.
- **Two ingestion code paths**: The REST API and Kafka consumer both insert metrics, meaning ingestion logic must be maintained and tested in two places.
- **Configuration surface**: The `KAFKA_ENABLED` flag creates a conditional code path that must be tested in both states. Integration tests must cover both configurations.
- **Eventual consistency**: Metrics ingested via Kafka are not immediately queryable. There is a small delay (typically sub-second) between publishing and database availability.
- **Consumer scaling**: The Kafka consumer must be scaled independently of the API. Under-provisioned consumers create consumer lag, delaying metric availability.
