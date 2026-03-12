# api/middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Histogram, Counter, Gauge

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        # Normalize path to avoid high-cardinality labels
        path = request.url.path
        for segment in path.split("/"):
            if segment and (len(segment) > 30 or _looks_like_id(segment)):
                path = path.replace(segment, "{id}")

        http_requests_in_progress.labels(method=method).inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            http_request_duration_seconds.labels(method=method, path=path, status_code=status_code).observe(duration)
            http_requests_total.labels(method=method, path=path, status_code=status_code).inc()
            http_requests_in_progress.labels(method=method).dec()

        return response


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add Deprecation header to legacy routes (without /api/v1/ prefix)."""

    LEGACY_PREFIXES = (
        "/metrics", "/dimensions", "/rules", "/ml/", "/alerts",
        "/data", "/webhooks", "/admin", "/incidents", "/forecasts",
        "/auth", "/audit",
    )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api/v1") and any(path.startswith(p) for p in self.LEGACY_PREFIXES):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-09-01"
            response.headers["Link"] = f'</api/v1{path}>; rel="successor-version"'
        return response


def _looks_like_id(segment: str) -> bool:
    """Heuristic: UUIDs, numeric IDs, hex strings."""
    if segment.isdigit():
        return True
    if len(segment) == 36 and segment.count("-") == 4:
        return True
    try:
        if len(segment) >= 8:
            int(segment, 16)
            return True
    except ValueError:
        pass
    return False
