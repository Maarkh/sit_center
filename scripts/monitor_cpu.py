#!/usr/bin/env python
"""Local metric collector (M1 bridge): ingest metrics into the DSS time-series
(canonical_metrics) from the ENABLED data sources in the registry — not a hardcoded
list. It re-reads `data_sources` every tick, so adding/editing a source in the admin
UI (Settings → Data sources) changes what gets collected, live.

Handled here (push/pull collectors that run on this host):
  host_agent — psutil metrics of this machine (cpu/mem/disk/...)
  http_pull  — GET a JSON endpoint on the source's interval and extract values
(kafka sources are consumed by core/kafka_consumer.py, not here.)

If no host_agent source is configured at all, it falls back to cpu_usage/mem_usage
under source='host' so the demo never goes dark.

All DSS processing (evaluate deviations, correlate situations, predict, escalate,
SLA breaches) runs in the Celery beat + worker, exactly as in production — start them
with scripts/run_celery.sh. This collector only produces metrics.

Prereqs: project env exported (DATABASE_URL, REDIS_*, …) and `PYTHONPATH=.`.

    PYTHONPATH=. python scripts/monitor_cpu.py

Env knobs: SAMPLE_SECONDS (5) — base tick / default host_agent interval.
"""
import os
import time

from sqlalchemy import text

from core.database import get_engine
from core.data_sources import active_sources, collect_host_agent, collect_http_pull

SAMPLE = int(os.environ.get("SAMPLE_SECONDS", "5"))
TENANT = os.environ.get("COLLECTOR_TENANT", "default")

_INSERT = text(
    "INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
    "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, :s, :t)"
)


def _gather(http_last):
    """Collect one round from the registry. Returns (rows, base_tick) where rows is
    a list of (metric_name, value, source_name)."""
    rows = []
    host_sources = active_sources("host_agent", TENANT)
    if host_sources:
        for s in host_sources:
            for m, v in collect_host_agent(s["config"]):
                rows.append((m, v, s["name"]))
        ticks = [int(s["config"].get("sample_seconds", SAMPLE)) for s in host_sources]
        base_tick = max(1, min(ticks)) if ticks else SAMPLE
    else:
        # no source configured → keep the lights on with the classic host metrics
        for m, v in collect_host_agent({"metrics": ["cpu_usage", "mem_usage"]}):
            rows.append((m, v, "host"))
        base_tick = SAMPLE

    now = time.monotonic()
    for s in active_sources("http_pull", TENANT):
        interval = int(s["config"].get("interval_seconds", 30))
        if now - http_last.get(s["id"], 0.0) >= interval:
            http_last[s["id"]] = now
            try:
                for m, v in collect_http_pull(s["config"]):
                    rows.append((m, v, s["name"]))
            except Exception as e:
                print(f"⚠️  http_pull '{s['name']}' failed: {e}")
    return rows, base_tick


def main():
    import psutil
    eng = get_engine()
    psutil.cpu_percent(interval=None)  # prime non-blocking cpu sampling
    print(f"📈 collector reading data_sources (tenant={TENANT}) → canonical_metrics. "
          f"DSS processing runs in Celery beat/worker. Ctrl-C to stop.")
    http_last: dict = {}
    while True:
        base_tick = SAMPLE
        try:
            rows, base_tick = _gather(http_last)
            if rows:
                with eng.begin() as c:
                    for m, v, src in rows:
                        c.execute(_INSERT, {"m": m, "v": float(v), "s": src, "t": TENANT})
                print(", ".join(f"{m}={v:.1f}@{src}" for m, v, src in rows))
        except Exception as e:
            print(f"⚠️  collect round failed: {e}")
        time.sleep(base_tick)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 stopped.")
