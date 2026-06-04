#!/usr/bin/env python
"""Local metric collector: sample this machine's CPU & RAM into the DSS time-series
(canonical_metrics). Acts like a host agent — the data source for the decision loop.

All DSS processing (evaluate deviations, correlate situations, predict, escalate,
SLA breaches) runs in the Celery beat + worker, exactly as in production — start them
with scripts/run_celery.sh. This collector only produces metrics.

Prereqs: project env exported (DATABASE_URL, REDIS_*, …) and `PYTHONPATH=.`.

    PYTHONPATH=. python scripts/monitor_cpu.py

Env knobs: SAMPLE_SECONDS (5).
"""
import os
import psutil
from sqlalchemy import text

from core.database import get_engine

SAMPLE = int(os.environ.get("SAMPLE_SECONDS", "5"))
TENANT = "default"

_INSERT = text(
    "INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
    "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'host', :t)"
)


def main():
    eng = get_engine()
    print(f"📈 collecting CPU/RAM → canonical_metrics every {SAMPLE}s. "
          f"DSS processing runs in Celery beat/worker. Ctrl-C to stop.")
    psutil.cpu_percent(interval=None)  # prime
    while True:
        cpu = psutil.cpu_percent(interval=SAMPLE)   # blocks ~SAMPLE seconds
        mem = psutil.virtual_memory().percent
        with eng.begin() as c:
            c.execute(_INSERT, {"m": "cpu_usage", "v": cpu, "t": TENANT})
            c.execute(_INSERT, {"m": "mem_usage", "v": mem, "t": TENANT})
        print(f"cpu={cpu:5.1f}% mem={mem:5.1f}%")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 stopped.")
