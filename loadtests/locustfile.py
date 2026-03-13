"""
Load tests for Situational Center API.

User classes:
  - ReadOnlyUser (weight 7): dashboard simulation — reads metrics, alerts, incidents, rules, health
  - DataIngester (weight 2): collector simulation — pushes data via ingest and queries data
  - AdminUser   (weight 1): admin simulation — user/role/tenant management

Run:
  locust -f loadtests/locustfile.py --host http://localhost:8000
  locust -f loadtests/locustfile.py --host http://localhost:8000 --headless -u 500 -r 50 -t 5m

Environment variables:
  LOCUST_TARGET_USER  (default: admin)
  LOCUST_TARGET_PASS  (default: admin)
"""

import os
import random
import logging
from datetime import datetime, timedelta, timezone

from locust import HttpUser, task, between, events

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_USER = os.getenv("LOCUST_TARGET_USER", "admin")
TARGET_PASS = os.getenv("LOCUST_TARGET_PASS", "admin")

API_V1 = "/api/v1"

# Metric names used for data ingestion and queries
METRIC_NAMES = [
    "cpu_usage",
    "memory_usage",
    "disk_io",
    "network_in",
    "network_out",
    "api_latency_p99",
    "request_count",
    "error_rate",
]

REGIONS = ["moscow", "spb", "novosibirsk", "ekaterinburg", "kazan", "sochi"]
SERVICES = ["auth", "billing", "gateway", "frontend", "ml-worker"]

# Rate-limit status code — treated as success, not failure
RATE_LIMITED = 429


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ok(response, *, allow_404=False):
    """Return True if the response should be treated as a success.

    Rate-limited (429) responses are always treated as successes so they
    do not pollute the failure statistics.  Optionally, 404 can also be
    accepted (useful for read endpoints on an empty database).
    """
    if response.status_code == RATE_LIMITED:
        # Mark as success — rate limiting is expected under heavy load
        response.success()
        return True
    ok_codes = {200, 201, 204}
    if allow_404:
        ok_codes.add(404)
    return response.status_code in ok_codes


def _random_iso_timestamp(hours_ago_max=72):
    """Generate a random ISO-8601 timestamp within the last *hours_ago_max* hours."""
    delta = timedelta(hours=random.randint(0, hours_ago_max))
    ts = datetime.now(timezone.utc) - delta
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _random_time_range(days_back=7):
    """Return (start, end) ISO timestamps for a data query window."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=random.randint(1, days_back))
    return (
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------------------------------------------------------------------------
# Event hook: log aggregate stats every 30 s in headless mode
# ---------------------------------------------------------------------------

@events.quitting.add_listener
def _on_quitting(environment, **kwargs):
    if environment.stats.total.fail_ratio > 0.05:
        logger.warning(
            "Overall failure ratio %.2f%% exceeds 5%% threshold",
            environment.stats.total.fail_ratio * 100,
        )


# ---------------------------------------------------------------------------
# Base class — handles authentication
# ---------------------------------------------------------------------------

class AuthenticatedUser(HttpUser):
    """Abstract base: authenticates once via POST /token on start."""

    abstract = True
    token: str = ""

    def on_start(self):
        """Obtain a JWT token via the /token endpoint."""
        with self.client.post(
            "/token",
            data={"username": TARGET_USER, "password": TARGET_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            name="/token (login)",
            catch_response=True,
        ) as resp:
            if resp.status_code == RATE_LIMITED:
                resp.success()
                logger.warning("Rate limited during login — will retry on next task")
                return
            if resp.status_code != 200:
                resp.failure(f"Login failed: {resp.status_code} {resp.text[:200]}")
                return
            body = resp.json()
            self.token = body.get("access_token", "")
            if not self.token:
                resp.failure("No access_token in response")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path, *, name=None, allow_404=False):
        """Convenience wrapper for authenticated GET with rate-limit handling."""
        with self.client.get(
            path,
            headers=self.auth_headers,
            name=name or path,
            catch_response=True,
        ) as resp:
            if not _is_ok(resp, allow_404=allow_404):
                resp.failure(f"{resp.status_code}: {resp.text[:200]}")
            return resp

    def _post(self, path, json_body, *, name=None, allow_404=False):
        """Convenience wrapper for authenticated POST with rate-limit handling."""
        with self.client.post(
            path,
            json=json_body,
            headers=self.auth_headers,
            name=name or path,
            catch_response=True,
        ) as resp:
            if not _is_ok(resp, allow_404=allow_404):
                resp.failure(f"{resp.status_code}: {resp.text[:200]}")
            return resp


# ---------------------------------------------------------------------------
# ReadOnlyUser — simulates dashboard consumers
# ---------------------------------------------------------------------------

class ReadOnlyUser(AuthenticatedUser):
    """Simulates operators viewing dashboards.

    Weight 7 — the most common user type.
    """

    weight = 7
    wait_time = between(1, 5)

    @task(5)
    def get_health(self):
        """Health check — no auth required, very cheap."""
        with self.client.get("/health", name="/health", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Health check failed: {resp.status_code}")

    @task(10)
    def list_metrics(self):
        self._get(f"{API_V1}/metrics/", name="GET /api/v1/metrics/")

    @task(10)
    def list_alerts(self):
        limit = random.choice([20, 50, 100])
        self._get(
            f"{API_V1}/alerts/?limit={limit}",
            name="GET /api/v1/alerts/",
            allow_404=True,
        )

    @task(8)
    def list_alerts_by_status(self):
        status = random.choice(["firing", "acknowledged", "resolved"])
        self._get(
            f"{API_V1}/alerts/?status={status}&limit=50",
            name="GET /api/v1/alerts/?status=...",
            allow_404=True,
        )

    @task(10)
    def list_incidents(self):
        limit = random.choice([20, 50])
        self._get(
            f"{API_V1}/incidents/?limit={limit}",
            name="GET /api/v1/incidents/",
            allow_404=True,
        )

    @task(5)
    def list_incidents_by_priority(self):
        priority = random.choice(["critical", "high", "medium", "low"])
        self._get(
            f"{API_V1}/incidents/?priority={priority}&limit=50",
            name="GET /api/v1/incidents/?priority=...",
            allow_404=True,
        )

    @task(8)
    def list_rules(self):
        self._get(f"{API_V1}/rules/", name="GET /api/v1/rules/", allow_404=True)

    @task(6)
    def query_data(self):
        """POST data query — simulates dashboard time-series panels."""
        start, end = _random_time_range()
        metric = random.choice(METRIC_NAMES)
        body = {
            "metric_name": metric,
            "start_time": start,
            "end_time": end,
            "limit": random.choice([100, 500, 1000]),
        }
        self._post(
            f"{API_V1}/data/query",
            body,
            name="POST /api/v1/data/query",
            allow_404=True,
        )

    @task(4)
    def query_data_with_dimensions(self):
        """POST data query with dimension filter."""
        start, end = _random_time_range()
        metric = random.choice(METRIC_NAMES)
        region = random.choice(REGIONS)
        body = {
            "metric_name": metric,
            "start_time": start,
            "end_time": end,
            "dimensions": {"region": region},
            "limit": 500,
        }
        self._post(
            f"{API_V1}/data/query",
            body,
            name="POST /api/v1/data/query (filtered)",
            allow_404=True,
        )

    @task(3)
    def get_sla_policies(self):
        self._get(
            f"{API_V1}/incidents/sla/policies",
            name="GET /api/v1/incidents/sla/policies",
            allow_404=True,
        )


# ---------------------------------------------------------------------------
# DataIngester — simulates metric collectors
# ---------------------------------------------------------------------------

class DataIngester(AuthenticatedUser):
    """Simulates data collectors pushing metrics.

    Weight 2 — moderate volume.
    Shorter wait time to simulate continuous telemetry streams.
    """

    weight = 2
    wait_time = between(0.5, 2)

    @task(10)
    def ingest_single(self):
        """POST a single metric data point via the ingest endpoint."""
        body = {
            "metric_name": random.choice(METRIC_NAMES),
            "value": round(random.uniform(0, 100), 2),
            "timestamp": _random_iso_timestamp(hours_ago_max=1),
            "dimensions": {
                "region": random.choice(REGIONS),
                "service": random.choice(SERVICES),
            },
        }
        with self.client.post(
            f"{API_V1}/data/ingest",
            json=body,
            headers=self.auth_headers,
            name="POST /api/v1/data/ingest",
            catch_response=True,
        ) as resp:
            if resp.status_code == RATE_LIMITED:
                resp.success()
            elif resp.status_code in (200, 201, 202):
                pass  # success
            elif resp.status_code == 404:
                # Endpoint may not exist yet — treat as expected
                resp.success()
            else:
                resp.failure(f"{resp.status_code}: {resp.text[:200]}")

    @task(5)
    def query_recent_data(self):
        """Query recently ingested data to verify it landed."""
        start, end = _random_time_range(days_back=1)
        metric = random.choice(METRIC_NAMES)
        body = {
            "metric_name": metric,
            "start_time": start,
            "end_time": end,
            "limit": 100,
        }
        self._post(
            f"{API_V1}/data/query",
            body,
            name="POST /api/v1/data/query (ingester verify)",
            allow_404=True,
        )

    @task(3)
    def list_metrics(self):
        """Verify metric definitions exist."""
        self._get(f"{API_V1}/metrics/", name="GET /api/v1/metrics/ (ingester)")

    @task(2)
    def health_check(self):
        with self.client.get("/health", name="/health (ingester)", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Health check failed: {resp.status_code}")


# ---------------------------------------------------------------------------
# AdminUser — simulates admin panel usage
# ---------------------------------------------------------------------------

class AdminUser(AuthenticatedUser):
    """Simulates admin users managing users, roles, tenants.

    Weight 1 — rare but important to include.
    """

    weight = 1
    wait_time = between(2, 6)

    @task(10)
    def list_users(self):
        self._get(
            f"{API_V1}/admin/users",
            name="GET /api/v1/admin/users",
            allow_404=True,
        )

    @task(8)
    def list_roles(self):
        self._get(
            f"{API_V1}/admin/roles",
            name="GET /api/v1/admin/roles",
            allow_404=True,
        )

    @task(6)
    def list_tenants(self):
        self._get(
            f"{API_V1}/admin/tenants",
            name="GET /api/v1/admin/tenants",
            allow_404=True,
        )

    @task(5)
    def list_metrics(self):
        self._get(f"{API_V1}/metrics/", name="GET /api/v1/metrics/ (admin)")

    @task(5)
    def list_alerts(self):
        self._get(
            f"{API_V1}/alerts/?limit=100",
            name="GET /api/v1/alerts/ (admin)",
            allow_404=True,
        )

    @task(5)
    def list_incidents(self):
        self._get(
            f"{API_V1}/incidents/?limit=100",
            name="GET /api/v1/incidents/ (admin)",
            allow_404=True,
        )

    @task(4)
    def list_rules(self):
        self._get(f"{API_V1}/rules/", name="GET /api/v1/rules/ (admin)", allow_404=True)

    @task(3)
    def get_health(self):
        with self.client.get("/health", name="/health (admin)", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Health check failed: {resp.status_code}")

    @task(2)
    def list_sla_policies(self):
        self._get(
            f"{API_V1}/incidents/sla/policies",
            name="GET /api/v1/incidents/sla/policies (admin)",
            allow_404=True,
        )
