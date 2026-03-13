# ADR-002: Redis Pub/Sub for WebSocket Alert Delivery

## Status

Accepted

## Date

2025-11-20

## Context

The Sit Center dashboard displays real-time alerts to operators monitoring infrastructure health. The original implementation used a polling-based approach: the frontend WebSocket handler queried the database every few seconds for new alerts, then pushed them to connected clients.

This design had significant drawbacks:

- **High latency**: Alerts were delayed by the polling interval (typically 3-5 seconds), which is unacceptable for critical infrastructure events.
- **Database load**: Each connected client generated periodic SELECT queries against the alerts table, creating unnecessary load proportional to the number of WebSocket connections.
- **Scaling issues**: With multiple API instances behind a load balancer, each instance polled independently, multiplying database pressure.
- **No fan-out**: Alert delivery was tightly coupled to the database query cycle, making it difficult to add additional consumers (e.g., mobile push, external integrations).

The system uses Redis (with hiredis) as its caching layer, so Redis is already a required infrastructure component.

## Decision

Use Redis Pub/Sub for real-time alert broadcast to WebSocket clients.

The architecture works as follows:

1. When a Celery task or alert processor detects an alert condition, it publishes an alert message to a Redis channel (e.g., `alerts:{tenant_id}`).
2. Each API instance runs a Redis subscriber that listens on the relevant alert channels.
3. The subscriber dispatches incoming messages to all connected WebSocket clients for that tenant.
4. Alert messages are also persisted to the database for history, but delivery to WebSocket clients does not depend on database reads.

Channel naming uses the pattern `alerts:{tenant_id}` to ensure tenant isolation at the Pub/Sub level.

## Consequences

### Positive

- **Sub-millisecond delivery**: Alerts reach WebSocket clients as soon as they are published, with no polling delay.
- **No database polling load**: WebSocket handlers no longer query the alerts table for new events, eliminating a significant source of read pressure.
- **Natural fan-out**: Redis Pub/Sub delivers messages to all subscribers simultaneously, supporting multiple API instances behind a load balancer without duplication.
- **Tenant isolation**: Per-tenant channels prevent cross-tenant alert leakage at the transport layer.
- **Extensibility**: Additional subscribers (logging, external webhooks) can be added to the same channels without modifying the alert publisher.

### Negative

- **Redis becomes critical path**: If Redis is unavailable, real-time alert delivery stops. Operators would need to fall back to manual dashboard refresh (alerts are still persisted to the database).
- **Message loss on disconnect**: Redis Pub/Sub is fire-and-forget. If no subscribers are connected when a message is published, the message is lost. This is acceptable because alerts are also persisted to the database, and clients can fetch missed alerts on reconnect.
- **No message history**: Unlike Redis Streams, Pub/Sub does not retain messages. Clients that connect after an alert is published must query the database for recent alerts.
- **Connection management**: Each API instance maintains a dedicated Redis connection for subscription, adding to the Redis connection pool requirements.
