#!/usr/bin/env python
"""Real local monitor: sample this machine's CPU & RAM into the DSS time-series and
drive the evaluation loop. A live, hands-on demo of the decision loop.

Prereqs: project env exported (DATABASE_URL, REDIS_*, …) and `PYTHONPATH=.`.
Run the setup (goal + indicators + playbook) first, then:

    PYTHONPATH=. python scripts/monitor_cpu.py

Env knobs: SAMPLE_SECONDS (5), EVAL_EVERY_SECONDS (30), EVAL_WINDOW_MIN (1).
In production this loop is the Celery beat task `evaluate_indicators_task`; here it
runs inline with a short window so breaches show up in the cockpit within ~a minute.
"""
import os
import time
import psutil
from sqlalchemy import text

from core.database import get_engine
from core.deviation_engine import indicator_evaluator
from core.situation_engine import situation_engine

SAMPLE = int(os.environ.get("SAMPLE_SECONDS", "5"))
EVAL_EVERY = int(os.environ.get("EVAL_EVERY_SECONDS", "30"))
EVAL_WINDOW_MIN = int(os.environ.get("EVAL_WINDOW_MIN", "1"))
TENANT = "default"

_INSERT = text(
    "INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
    "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'host', :t)"
)


def main():
    eng = get_engine()
    print(f"📈 monitoring CPU/RAM → canonical_metrics every {SAMPLE}s; "
          f"evaluating every {EVAL_EVERY}s (window {EVAL_WINDOW_MIN}m). Ctrl-C to stop.")
    psutil.cpu_percent(interval=None)  # prime
    elapsed = 0
    while True:
        cpu = psutil.cpu_percent(interval=SAMPLE)   # blocks ~SAMPLE seconds
        mem = psutil.virtual_memory().percent
        with eng.begin() as c:
            c.execute(_INSERT, {"m": "cpu_usage", "v": cpu, "t": TENANT})
            c.execute(_INSERT, {"m": "mem_usage", "v": mem, "t": TENANT})
        elapsed += SAMPLE
        if elapsed >= EVAL_EVERY:
            elapsed = 0
            s = indicator_evaluator.evaluate_tenant(TENANT, window_minutes=EVAL_WINDOW_MIN)
            sit = situation_engine.correlate_tenant(TENANT, window_minutes=30)
            print(f"cpu={cpu:5.1f}% mem={mem:5.1f}% | eval: breaching={s['breaching']} "
                  f"opened={s['opened']} chronic={s['chronic']} resolved={s['resolved']} "
                  f"recs={s.get('recommended', 0)} | situations: +{sit['created']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 stopped.")
