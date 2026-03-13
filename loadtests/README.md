# Load Testing — Situational Center API

Load tests for the Sit Center API built with [Locust](https://locust.io/).

## Prerequisites

```bash
pip install locust
```

## User Classes

| Class          | Weight | wait_time | Description                                  |
|----------------|--------|-----------|----------------------------------------------|
| `ReadOnlyUser` | 7      | 1-5 s     | Dashboard consumers: metrics, alerts, incidents, rules, data queries |
| `DataIngester` | 2      | 0.5-2 s   | Metric collectors: data ingest + verification queries |
| `AdminUser`    | 1      | 2-6 s     | Admin panel: users, roles, tenants management |

With 500 concurrent users this yields roughly 350 readers, 100 ingesters, and 50 admins.

## Environment Variables

| Variable             | Default | Description              |
|----------------------|---------|--------------------------|
| `LOCUST_TARGET_USER` | `admin` | Username for /token auth |
| `LOCUST_TARGET_PASS` | `admin` | Password for /token auth |

## Running

### Web UI (default)

```bash
locust -f loadtests/locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 in a browser, set the number of users and spawn rate.

### Headless — 500 users, ramp 50/s, run 5 minutes

```bash
locust -f loadtests/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    -u 500 \
    -r 50 \
    -t 5m
```

### Custom credentials

```bash
LOCUST_TARGET_USER=operator LOCUST_TARGET_PASS=secret123 \
    locust -f loadtests/locustfile.py --host http://localhost:8000 --headless -u 500 -r 50 -t 5m
```

### Save HTML report

```bash
locust -f loadtests/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    -u 500 -r 50 -t 5m \
    --html loadtests/report.html
```

### Save CSV stats

```bash
locust -f loadtests/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    -u 500 -r 50 -t 5m \
    --csv loadtests/stats
```

This creates `stats_stats.csv`, `stats_stats_history.csv`, and `stats_failures.csv`.

## Rate Limiting

The API enforces rate limits (100/min global, 5/min on /token, 30/min on data ingest/incidents).
HTTP 429 responses are handled gracefully and counted as successes in Locust statistics
so they do not skew failure metrics.

## Endpoints Covered

- `GET  /health` — health check (no auth)
- `POST /token` — authentication (once per user on start)
- `GET  /api/v1/metrics/` — list metric definitions
- `GET  /api/v1/alerts/` — list alerts (with status/limit filters)
- `GET  /api/v1/incidents/` — list incidents (with priority/limit filters)
- `GET  /api/v1/incidents/sla/policies` — SLA policies
- `GET  /api/v1/rules/` — list alert rules
- `POST /api/v1/data/query` — time-series data queries (plain and filtered)
- `POST /api/v1/data/ingest` — data ingestion
- `GET  /api/v1/admin/users` — admin: list users
- `GET  /api/v1/admin/roles` — admin: list roles
- `GET  /api/v1/admin/tenants` — admin: list tenants
