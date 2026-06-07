# core/data_sources.py
# M1 Ingestion — the data-source registry's runtime side. Pure-ish helpers used by
# both the API (probe/test) and the collectors (scripts/monitor_cpu.py reads
# host_agent + http_pull; core/kafka_consumer.py reads kafka). Keeping the transport
# logic here (not in the route) lets the collector reuse it without importing FastAPI.
from typing import Any, Dict, List, Tuple

from sqlalchemy import text

from core.database import get_engine
from config import logger

SOURCE_TYPES = ["host_agent", "http_pull", "kafka", "http_push"]

# external agents POST to this path with the source's api_key in the X-API-KEY header
INGEST_PATH = "/api/v1/ingest/metrics"

# config keys whose values are masked on read and preserved-on-"***" on update
SECRET_KEYS = {"token", "password", "api_key", "secret", "auth_token", "sasl_password"}


# ── host_agent ──────────────────────────────────────────────────────────────
# metric_name -> zero-arg callable returning a float. cpu_usage is non-blocking
# (interval=None): it reports utilisation since the previous call, so the collector
# primes it once at startup and probe() primes it inline.
def _cpu() -> float:
    import psutil
    return float(psutil.cpu_percent(interval=None))


def _mem() -> float:
    import psutil
    return float(psutil.virtual_memory().percent)


def _disk() -> float:
    import psutil
    return float(psutil.disk_usage("/").percent)


def _swap() -> float:
    import psutil
    return float(psutil.swap_memory().percent)


def _load1() -> float:
    import os
    return float(os.getloadavg()[0])


HOST_METRICS = {
    "cpu_usage": _cpu,
    "mem_usage": _mem,
    "disk_usage": _disk,
    "swap_usage": _swap,
    "load1": _load1,
}


def collect_host_agent(config: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Read the host metrics named in config['metrics'] via psutil. Unknown names
    are skipped (logged once by the caller). Returns [(metric_name, value), ...]."""
    wanted = config.get("metrics") or ["cpu_usage", "mem_usage"]
    out: List[Tuple[str, float]] = []
    for name in wanted:
        fn = HOST_METRICS.get(name)
        if fn is None:
            continue
        try:
            out.append((name, fn()))
        except Exception as e:  # a single metric failing must not kill the loop
            logger.warning("host_agent metric %s failed: %s", name, e)
    return out


# ── http_pull ───────────────────────────────────────────────────────────────
def _dig(obj: Any, path: str) -> Any:
    """Walk a dotted json path: 'data.items.0.value' → obj['data']['items'][0]['value']."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def collect_http_pull(config: Dict[str, Any], timeout: int = 10) -> List[Tuple[str, float]]:
    """GET config['url'] and extract each metric_map entry's json_path → value.
    metric_map: [{"json_path": "data.cpu", "metric_name": "ext_cpu"}, ...]."""
    import requests

    url = config.get("url")
    if not url:
        raise ValueError("http_pull source has no 'url'")
    headers = dict(config.get("headers") or {})
    token = config.get("token")
    if token:
        headers.setdefault("Authorization", f"Bearer {token}")
    method = (config.get("method") or "GET").upper()
    resp = requests.request(method, url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()

    out: List[Tuple[str, float]] = []
    for m in config.get("metric_map") or []:
        jp, name = m.get("json_path"), m.get("metric_name")
        if not jp or not name:
            continue
        try:
            out.append((name, float(_dig(payload, jp))))
        except Exception as e:
            logger.warning("http_pull %s path %s failed: %s", name, jp, e)
    return out


# ── probe (used by the /test endpoint) ──────────────────────────────────────
def probe(stype: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort liveness check returning a small sample. Never raises — returns
    {"ok": bool, ...}."""
    try:
        if stype == "host_agent":
            try:
                import psutil
                psutil.cpu_percent(interval=0.2)  # prime so cpu_usage reports a real number
            except Exception:
                pass
            readings = collect_host_agent(config)
            return {"ok": True, "sample": {k: v for k, v in readings}}
        if stype == "http_pull":
            readings = collect_http_pull(config)
            return {"ok": True, "sample": {k: v for k, v in readings}}
        if stype == "kafka":
            topic = config.get("topic")
            if not topic:
                return {"ok": False, "error": "kafka source has no 'topic'"}
            # We don't open a broker connection here (it may be disabled in this env);
            # the consumer picks the topic up from the registry when KAFKA_ENABLED.
            return {"ok": True, "sample": {"topic": topic}}
        if stype == "http_push":
            # inbound source — nothing to call; just report readiness
            return {"ok": True, "sample": {"api_key_set": bool(config.get("api_key")),
                                           "endpoint": INGEST_PATH}}
        return {"ok": False, "error": f"unknown type {stype}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── registry queries (used by the collectors) ───────────────────────────────
def active_sources(stype: str, tenant_id: str = "default") -> List[Dict[str, Any]]:
    """Enabled sources of one type for a tenant. Returns plain dicts (id, name,
    type, config) so callers don't depend on SQLAlchemy row objects."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, type, config FROM data_sources "
                 "WHERE tenant_id = :tid AND type = :t AND enabled = true ORDER BY name"),
            {"tid": tenant_id, "t": stype},
        ).mappings().all()
    return [{"id": str(r["id"]), "name": r["name"], "type": r["type"], "config": r["config"] or {}}
            for r in rows]


def active_tenant_ids() -> List[str]:
    """Active tenant ids, falling back to ['default'] if the tenants table is absent
    or unreadable. Mirrors the Celery tasks' tenant loop (core/ml_tasks.py,
    core/dss_tasks.py) without importing Celery — so the collector can reuse it."""
    try:
        with get_engine().connect() as conn:
            rows = conn.execute(text("SELECT id FROM tenants WHERE is_active = true")).scalars().all()
        return list(rows) or ["default"]
    except Exception:
        return ["default"]


# ── kafka topic resolution (used by core/kafka_consumer.py) ──────────────────
def kafka_topics_from_sources(sources: List[Dict[str, Any]], default_topic: str = None) -> List[str]:
    """Distinct topics declared by kafka sources, plus the default env topic for
    back-compat. Order-preserving, deduplicated."""
    topics = [(s.get("config") or {}).get("topic") for s in sources]
    if default_topic:
        topics.append(default_topic)
    seen, out = set(), []
    for t in topics:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def resolve_kafka_topics(default_topic: str = None, tenant_id: str = "default") -> List[str]:
    """Topics the consumer should subscribe to: the enabled kafka sources' topics
    unioned with the default env topic. Falls back to just the default if the
    registry can't be read (old deploy / DB down at startup)."""
    try:
        sources = active_sources("kafka", tenant_id)
    except Exception as e:
        logger.warning("kafka source registry unavailable, using default topic: %s", e)
        sources = []
    return kafka_topics_from_sources(sources, default_topic)


def kafka_bootstrap_from_sources(sources: List[Dict[str, Any]], default_servers: str = None) -> str:
    """First non-empty bootstrap_servers declared by a kafka source, else the default.
    A single consumer connects to ONE cluster, so if sources disagree the first wins
    (logged)."""
    declared = [(s.get("config") or {}).get("bootstrap_servers") for s in sources]
    declared = [d for d in declared if d]
    if not declared:
        return default_servers
    uniq = list(dict.fromkeys(declared))
    if len(uniq) > 1:
        logger.warning("multiple kafka bootstrap_servers declared %s; using %s", uniq, uniq[0])
    return uniq[0]


def resolve_kafka_bootstrap(default_servers: str = None, tenant_id: str = "default") -> str:
    """Prefer a registry kafka source's bootstrap_servers over the env default."""
    try:
        sources = active_sources("kafka", tenant_id)
    except Exception as e:
        logger.warning("kafka source registry unavailable, using default bootstrap: %s", e)
        sources = []
    return kafka_bootstrap_from_sources(sources, default_servers)


# ── http_push ingestion (used by api/routes/ingestion.py) ────────────────────
def find_source_by_api_key(api_key: str):
    """Locate the enabled http_push source whose config.api_key matches. The key
    identifies both the tenant and the source. Returns {id, tenant_id, name} or None."""
    if not api_key:
        return None
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, tenant_id, name FROM data_sources "
                 "WHERE type = 'http_push' AND enabled = true AND config->>'api_key' = :k LIMIT 1"),
            {"k": api_key},
        ).mappings().first()
    if not row:
        return None
    return {"id": str(row["id"]), "tenant_id": row["tenant_id"], "name": row["name"]}


# Use CAST(... AS ...) not the ':: ' operator — SQLAlchemy text() mis-parses a bind
# param immediately followed by '::', leaving it unconverted (psycopg2 syntax error).
_METRIC_INSERT = text(
    "INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
    "VALUES (:metric_name, :value, COALESCE(CAST(:timestamp AS timestamptz), NOW()), "
    "CAST(:dimensions AS jsonb), CAST(:tags AS jsonb), :source, :tenant_id)"
)


def build_metric_rows(points, source_name: str, tenant_id: str) -> List[Dict[str, Any]]:
    """Shape ingested points into canonical_metrics insert params. Accepts dicts or
    objects exposing metric_name/value/timestamp/dimensions/tags."""
    import json

    def field(p, k):
        return p.get(k) if isinstance(p, dict) else getattr(p, k, None)

    rows = []
    for p in points:
        rows.append({
            "metric_name": field(p, "metric_name"),
            "value": float(field(p, "value")),
            "timestamp": field(p, "timestamp"),
            "dimensions": json.dumps(field(p, "dimensions") or {}),
            "tags": json.dumps(field(p, "tags") or {}),
            "source": source_name,
            "tenant_id": tenant_id,
        })
    return rows


def insert_metrics(points, source_name: str, tenant_id: str) -> int:
    """Bulk-insert ingested points into canonical_metrics under the given source name
    and tenant. Returns the number of rows written."""
    rows = build_metric_rows(points, source_name, tenant_id)
    if not rows:
        return 0
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(_METRIC_INSERT, rows)
    return len(rows)
