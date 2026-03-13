# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Sit Center project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. Each ADR describes a single decision and is immutable once accepted. If a decision is reversed or superseded, a new ADR is created referencing the old one.

## ADR Format

Each ADR follows this standard template:

- **Title** -- Short noun phrase describing the decision
- **Status** -- Proposed, Accepted, Deprecated, or Superseded
- **Date** -- When the decision was made
- **Context** -- The forces at play, including technical, political, and project-specific constraints
- **Decision** -- The change being proposed or enacted
- **Consequences** -- What becomes easier or harder as a result of this decision

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-timescaledb-over-manual-partitioning.md) | TimescaleDB Over Manual Partitioning | Accepted |
| [002](002-redis-pubsub-for-websocket.md) | Redis Pub/Sub for WebSocket Alert Delivery | Accepted |
| [003](003-multi-tenancy-shared-database.md) | Multi-Tenancy via Shared Database with tenant_id | Accepted |
| [004](004-kafka-optional-ingestion.md) | Kafka as Optional Ingestion Layer | Accepted |
| [005](005-vault-for-secrets.md) | HashiCorp Vault for Secret Management | Accepted |
