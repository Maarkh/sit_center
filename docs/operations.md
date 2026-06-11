# Operations Guide

This document covers operational topics for the Sit Center platform: authentication flows, data retention, secret management, database tuning, caching, and overload protection.

---

## 1. JWT Authentication Flow

### Local Authentication

1. Client sends `POST /token` with form-encoded body containing `username` and `password`.
2. Server validates credentials against the local database (or LDAP if configured).
3. On success, returns:
   ```json
   {"access_token": "...", "token_type": "bearer"}
   ```
4. The JWT payload contains the following claims:
   - `sub` -- username
   - `tenant_id` -- tenant scope for multi-tenancy
   - `roles` -- list of assigned roles
   - `permissions` -- list of granular permissions
   - `scopes` -- OAuth2 scopes
   - `exp` -- expiration timestamp
5. Token expires in 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=30`).
6. There is no refresh token mechanism. When the token expires, the client must re-authenticate by calling `POST /token` again.

### Frontend Token Handling

- The frontend stores the token in `localStorage`.
- On application init, the `isTokenExpired` utility checks the `exp` claim. If expired, the user is redirected to login.

### OIDC Authentication (Keycloak)

1. Client navigates to `GET /auth/login/oidc`, which redirects the browser to the Keycloak authorization endpoint.
2. After the user authenticates with Keycloak, the browser is redirected back to `GET /auth/callback/oidc`.
3. The callback handler exchanges the authorization code for Keycloak tokens, extracts user information, and issues a local JWT with the same structure as local authentication.

---

## 2. Audit Log Retention

### Schema

Audit entries are stored in the `audit_log` table in PostgreSQL with the following fields:

| Field           | Type      | Description                          |
|-----------------|-----------|--------------------------------------|
| `username`      | text      | User who performed the action        |
| `tenant_id`     | text      | Tenant scope                         |
| `action`        | text      | Action performed (create, update, delete) |
| `resource_type` | text      | Type of resource affected            |
| `resource_id`   | text      | Identifier of the affected resource  |
| `changes`       | JSONB     | Before/after diff of the mutation    |
| `ip_address`    | text      | Client IP address                    |
| `user_agent`    | text      | Client user-agent string             |
| `timestamp`     | timestamptz | When the action occurred           |

All mutating endpoints call `core/audit.py::log_audit()` to write entries.

### Retention Policy

- **Online (queryable):** 90 days.
- **Archive:** Move entries older than 90 days to cold storage (compressed SQL dump).
- **Purge:** Delete archived entries from the live database.

### Archive Procedure (Monthly Cron)

```bash
# Archive audit entries older than 90 days
pg_dump -h db -U $POSTGRES_USER -t audit_log --data-only \
  --where="timestamp < NOW() - INTERVAL '90 days'" $POSTGRES_DB \
  | gzip > /backups/audit/audit_$(date +%Y%m).sql.gz
# Then purge
psql -h db -U $POSTGRES_USER $POSTGRES_DB \
  -c "DELETE FROM audit_log WHERE timestamp < NOW() - INTERVAL '90 days'"
```

Schedule this as a cron job on the first of each month. Verify the backup file is non-empty before running the DELETE.

---

## 3. Secret Rotation

### Vault Integration

The Vault integration lives in `core/vault.py` and supports three authentication methods:

- **Token auth** -- direct Vault token
- **AppRole auth** -- role_id + secret_id
- **Kubernetes SA auth** -- service account JWT mounted in the pod

Secrets are fetched at startup via `inject_vault_secrets()`. There is no hot-reload mechanism; a service restart is required after any secret change.

### General Rotation Procedure

1. Update the secret in Vault (or in `.env` for non-Vault deployments).
2. Perform a rolling restart of the affected services.
3. For database credential rotation specifically: ensure both old and new credentials are valid in PostgreSQL during the transition window to avoid downtime.

### Rotation Checklist by Secret

| Secret                | Impact of Rotation                                      | Services to Restart         |
|-----------------------|---------------------------------------------------------|-----------------------------|
| `SECRET_KEY`          | Invalidates all existing JWTs. All users must re-login. | API servers                 |
| `POSTGRES_PASSWORD`   | Update in both Vault and PostgreSQL before restart.      | API servers + Celery workers |
| `REDIS_PASSWORD`      | Update in both Vault and Redis before restart.           | All services (API, workers, WebSocket) |
| `I_DOIT_API_KEY`      | i-doit ITSM sync will fail until restart.               | Celery workers              |
| `TELEGRAM_BOT_TOKEN`  | Telegram notifications will fail until restart.          | Celery workers              |
| `WEBHOOK_API_KEY`     | External webhook producers must be notified of new key.  | Celery workers              |

---

## 4. TimescaleDB Tuning

### Hypertable Configuration

- **Hypertable:** `canonical_metrics`
- **Chunk interval:** 7 days
- **Compression:** Enabled at 30 days, with `segmentby=metric_name` and `orderby=timestamp DESC`
- **Retention:** Chunks older than 365 days are automatically dropped

### Continuous Aggregate

The `cagg_hourly_metrics` continuous aggregate is auto-refreshed and replaces the need for a manual materialized view. It pre-aggregates hourly rollups for dashboard queries.

### Recommended postgresql.conf (8 GB RAM Server)

```
shared_preload_libraries = 'timescaledb'
# Memory
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB
# TimescaleDB specific
timescaledb.max_background_workers = 8
max_parallel_workers_per_gather = 4
```

### Monitoring Queries

Check chunk count:

```sql
SELECT count(*)
FROM timescaledb_information.chunks
WHERE hypertable_name = 'canonical_metrics';
```

Check compression ratio:

```sql
SELECT * FROM hypertable_compression_stats('canonical_metrics');
```

A healthy system with 365-day retention and 7-day chunks should have roughly 52 chunks, minus any that have been dropped or not yet created.

---

## 5. Redis Memory Patterns

### Usage Areas

- **API caching:** TTL-based key/value cache for metric metadata and rule definitions.
- **Pub/Sub:** Real-time alert delivery to WebSocket clients via the `alerts` channel.
- **Rate limiting:** slowapi stores rate limit counters with auto-expiring keys.

### Key Naming Conventions

| Pattern                                  | Purpose                        |
|------------------------------------------|--------------------------------|
| `cache:metrics:<tenant_id>:<key>`        | Metric metadata cache          |
| `cache:rules:<tenant_id>`                | Rule definitions cache         |
| `alerts`                                 | Pub/Sub channel for WebSocket alert delivery |
| (managed by slowapi)                     | Rate limiter counters (auto-expiring) |

All cache keys include `tenant_id` to enforce multi-tenant isolation.

### Configuration Recommendations

- **Eviction policy:** `maxmemory-policy allkeys-lru` -- ensures Redis evicts least-recently-used keys when memory is full rather than returning errors.
- **Expected memory footprint:** Approximately 50 MB for 10K cached entries plus rate limiter state.
- **High availability:** Redis Sentinel with 3 nodes for automatic failover.

### Monitoring

```bash
redis-cli INFO memory
```

Key metrics to watch:

- `used_memory_human` -- current memory consumption
- `evicted_keys` -- non-zero means Redis is under memory pressure and evicting cached data

---

## 6. Backpressure and Overload Protection

### Rate Limiting

- Implementation: slowapi with Redis backend (`api/limiter.py`). Falls back to `memory://` in tests.
- **Global limit:** 100 requests per minute per IP.
- **Write endpoints:** 10--30 requests per minute depending on the route.
- **429 responses:** Include a `Retry-After` header. The Locust load tests treat 429 as a success (expected behavior under load).

### Kafka Consumer Backpressure

- The Kafka consumer (enabled via `KAFKA_ENABLED`) processes records in batches of 100.
- If the database insert is slow, consumer lag increases. Monitor via consumer group lag metrics.
- There is no explicit message shedding; the consumer will process all messages eventually.

### Celery Worker Overload

- Worker prefetch multiplier is 1 (one task fetched at a time per worker process).
- The dedicated ML worker uses `--max-tasks-per-child=10` to prevent memory leaks from TensorFlow/PyTorch model loading.
- If the task queue grows, tasks wait in the queue. There is no task shedding or priority-based dropping.

### Database Connection Pool

- SQLAlchemy configuration: `pool_size=5`, `max_overflow=10` (up to 15 connections per process).
- If the pool is exhausted, requests block for up to 30 seconds (`pool_timeout`).
- Monitor pool utilization via `sqlalchemy_pool_*` Prometheus metrics exposed by the middleware in `api/middleware.py`.

### WebSocket Connections

- `ConnectionManager` maintains an in-memory list of active WebSocket connections.
- There is no application-level connection limit. For production deployments, use nginx `limit_conn` to cap the number of concurrent WebSocket connections per IP.

### Health Check and Load Balancer Integration

- `GET /health` checks connectivity to PostgreSQL, Redis, and optionally Kafka and ClickHouse.
- Returns HTTP 200 when all dependencies are healthy, HTTP 503 when any dependency is degraded.
- Configure the load balancer to poll `/health` and remove instances that return 503.

## 7. DSS Decision Loop (background tasks)

The decision-support modules run a closed loop driven by Celery beat
(`celeryconfig.py`; tasks in `core/dss_tasks.py`). All are tenant-aware and safe to
run with no data (they no-op).

| Task | Schedule | Purpose |
|------|----------|---------|
| `evaluate_indicators_task` | every 2 min | Evaluate each active indicator against its corridor → write deviations / chronicle (M3). On a chronic crossing it auto-generates recommendations (M3→M7). |
| `correlate_situations_task` | every 3 min | Cluster active deviations into situations via the dependency graph + time window (M4). |
| `predict_indicators_task` | every 15 min | Forecast single-metric indicators (Prophet) and raise predictive alerts when the forecast/band will leave the corridor (M5). |
| `check_process_step_sla_task` | every 5 min | Escalate process step assignments past their `due_at` (M8). |
| `evaluate_decision_outcomes_task` | every 10 min | Auto-derive decision outcomes (completed process + resolved deviation = win) feeding playbook win-rate back into recommendation scoring (M10). |

Workers:

```bash
celery -A tasks.celery_app worker -l INFO     # general queue (DSS tasks)
celery -A tasks.celery_app beat   -l INFO     # scheduler
```

Without beat, every step is also reachable via the API (the cockpit's "Correlate",
"Generate recommendations", `POST /scenarios/{id}/run`, `POST /predictions/run`, etc.).

**Notes**
- Predictive forecasting needs `prophet` installed and ≥48 recent points; otherwise the
  task logs and skips (no crash).
- Indicator value = weighted average of its factors' metrics over the last ~5 minutes;
  an indicator with no recent data is skipped.
- See **[dss-guide.md](dss-guide.md)** for the full operator/developer walkthrough.

## 10. Row-Level Security (defense-in-depth tenant isolation)

The application filters every query by `tenant_id`. Migration `029` adds a DB-level
backstop: RLS policies on every tenant-scoped table so a query that forgets the filter
(or an injection) still cannot cross tenants.

**How it works (fail-open):**
- The web layer binds each request to the caller's tenant (`core/rls.py` sets
  `app.current_tenant` on the pooled connection at checkout, from a per-request
  ContextVar). The policy then restricts rows to that tenant.
- Workers, the collector, and migrations set no context → the policy allows all rows,
  so legitimate cross-tenant work is unaffected. `'*'` is an explicit bypass sentinel.
- Toggle with `RLS_ENABLED` (default `true`). The metrics hypertable
  `canonical_metrics` is excluded (TimescaleDB columnstore can't take RLS; it's
  append-only telemetry, already tenant-filtered in every query).

**⚠️ REQUIRED for RLS to actually enforce — run the app as a non-superuser role:**
PostgreSQL **bypasses RLS for SUPERUSER and BYPASSRLS roles** (and, without `FORCE`,
for the table owner — `FORCE` is set, but the superuser exemption still applies). If
the app connects as a superuser (common in dev), RLS is silently a no-op. In
production create a dedicated, least-privilege role:

```sql
CREATE ROLE sitcenter_app LOGIN PASSWORD '<strong>' NOSUPERUSER NOBYPASSRLS;
GRANT CONNECT ON DATABASE sit_center TO sitcenter_app;
GRANT USAGE ON SCHEMA public TO sitcenter_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sitcenter_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sitcenter_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sitcenter_app;
-- Run migrations as the owner/superuser; run the app (web + workers) as sitcenter_app.
```

Verify enforcement: `SET ROLE sitcenter_app; SELECT set_config('app.current_tenant','t1',false);`
then confirm a `SELECT` only returns tenant `t1` rows.
