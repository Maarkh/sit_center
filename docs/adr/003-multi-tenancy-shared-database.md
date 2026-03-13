# ADR-003: Multi-Tenancy via Shared Database with tenant_id

## Status

Accepted

## Date

2025-11-20

## Context

The Sit Center platform must support multiple organizational tenants, each with their own users, metrics, dashboards, alert rules, and incidents. The system targets 500+ users across multiple tenants.

Three multi-tenancy strategies were considered:

1. **Separate databases per tenant**: Full physical isolation. Each tenant gets a dedicated database instance.
2. **Shared database, separate schemas**: One database with a PostgreSQL schema per tenant. Tables are duplicated in each schema.
3. **Shared database, shared schema**: One database, one set of tables, with a `tenant_id` column on every table for row-level isolation.

Separate databases provide the strongest isolation but create significant operational overhead: migrations must be applied to every database, connection pooling becomes complex, and cross-tenant analytics (for superadmins) require federated queries.

Separate schemas reduce some operational burden but still duplicate table structures and complicate migrations.

The current user base and data volume do not justify the operational cost of physical isolation. The primary requirement is logical isolation with the ability for superadmin users to perform cross-tenant analytics.

## Decision

Use a shared database with a `tenant_id` column on all tables. Row-level isolation is enforced at the application layer:

- Every database table includes a non-nullable `tenant_id` column.
- All queries include a `WHERE tenant_id = :tenant_id` filter, with the tenant ID extracted from the authenticated user's JWT token.
- All cache keys in Redis include the tenant_id as a prefix (e.g., `{tenant_id}:metrics:summary`).
- API endpoints extract tenant_id from the JWT and pass it through the request context. There is no URL-based tenant identification.
- Superadmin users can query across tenants by omitting the tenant filter (controlled by RBAC permissions in the JWT).
- Database indexes on frequently queried tables include `tenant_id` as a leading column.

## Consequences

### Positive

- **Simple operations**: Single database to back up, migrate, monitor, and scale. One connection pool serves all tenants.
- **Easy cross-tenant analytics**: Superadmin dashboards can aggregate data across tenants with simple queries (no federated queries or cross-database joins).
- **No schema duplication**: Table definitions exist once. Migrations are applied once.
- **Resource efficiency**: Shared connection pools and shared TimescaleDB hypertables avoid per-tenant resource overhead.
- **Straightforward onboarding**: Adding a new tenant is an insert into the tenants table, not a database or schema provisioning operation.

### Negative

- **Application-layer isolation burden**: Every query, cache key, and API endpoint must correctly filter by tenant_id. A missing filter is a data leak. This must be enforced through code review, testing, and middleware.
- **Index bloat**: Adding `tenant_id` to every composite index increases index size across all tables. For TimescaleDB hypertables, this affects chunk indexes as well.
- **No physical isolation**: A noisy tenant with high query volume affects all tenants sharing the same database. There are no per-tenant resource quotas at the database level.
- **Compliance limitations**: Some regulatory environments require physical data isolation between tenants. This architecture does not satisfy that requirement without additional measures (e.g., row-level security policies in PostgreSQL).
- **Testing complexity**: All test fixtures and assertions must account for tenant_id to avoid false positives from cross-tenant data leakage.
