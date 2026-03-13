# ADR-001: TimescaleDB Over Manual Partitioning

## Status

Accepted

## Date

2025-11-20

## Context

The `canonical_metrics` table stores high-frequency time-series data from monitored infrastructure. The original design used manual monthly partitioning managed by a scheduled Celery task that created new partition tables and attached them to the parent.

This approach had several problems at scale:

- The Celery task was error-prone: if it failed or was delayed, inserts to the parent table would fail with missing partition errors.
- Manual partition management required custom DDL logic, monitoring, and rollback procedures.
- Compression and data retention were handled by separate Celery tasks with their own failure modes.
- Query performance degraded as partition count grew, because the planner had to evaluate all partitions without hypertable-level optimizations.
- Materialized view refresh for dashboards was a manual `REFRESH MATERIALIZED VIEW CONCURRENTLY` call, adding another moving part.

The system needed to support 500+ users with sub-second dashboard queries over 365 days of metric history.

## Decision

Migrate from manual PostgreSQL partitioning to TimescaleDB hypertables on the `canonical_metrics` table with the following configuration:

- **Chunk interval**: 7 days (balances query performance with chunk management overhead)
- **Compression policy**: Automatic compression of chunks older than 30 days (using TimescaleDB's built-in columnar compression)
- **Retention policy**: Automatic drop of chunks older than 365 days
- **Continuous aggregates**: Replace manually-refreshed materialized views with TimescaleDB continuous aggregates for dashboard rollups

The migration involves:

1. Installing the TimescaleDB extension on the PostgreSQL instance.
2. Converting the existing partitioned table to a hypertable via `create_hypertable()`.
3. Backfilling existing data into the new chunk structure.
4. Removing the Celery tasks for partition creation, compression, and retention.
5. Creating continuous aggregate policies for hourly and daily rollups.

## Consequences

### Positive

- **Automatic chunk management**: No more Celery tasks for partition creation. TimescaleDB creates chunks on demand as data arrives.
- **Built-in compression**: Columnar compression reduces storage by approximately 10x for older metric data, applied automatically by policy.
- **Retention automation**: Drop_chunks policy handles data expiry without custom code.
- **Continuous aggregates**: Real-time aggregation with automatic refresh replaces manual materialized view management.
- **Query optimization**: TimescaleDB's chunk exclusion and time-based indexing improve query planning over native partitioning.
- **Reduced operational risk**: Fewer custom Celery tasks means fewer failure modes to monitor and recover from.

### Negative

- **Extension dependency**: Requires the TimescaleDB extension to be installed and maintained on all PostgreSQL instances (development, staging, production).
- **Migration complexity**: Converting an existing partitioned table with live data requires careful planning and a maintenance window.
- **Vendor coupling**: Some TimescaleDB features (e.g., continuous aggregates, compression) use proprietary syntax not portable to vanilla PostgreSQL.
- **License considerations**: TimescaleDB community edition covers current needs, but advanced features (multi-node, certain policies) require the proprietary license.
