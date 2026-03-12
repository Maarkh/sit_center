# core/celery_metrics.py
import time
from prometheus_client import Histogram, Counter
from celery.signals import task_prerun, task_postrun, task_failure

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution duration in seconds",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

celery_task_failures_total = Counter(
    "celery_task_failures_total",
    "Total Celery task failures",
    ["task_name"],
)

_task_start_times = {}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, **kwargs):
    _task_start_times[task_id] = time.perf_counter()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, **kwargs):
    start = _task_start_times.pop(task_id, None)
    if start is not None:
        duration = time.perf_counter() - start
        task_name = getattr(sender, "name", "unknown")
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


@task_failure.connect
def task_failure_handler(sender=None, **kwargs):
    task_name = getattr(sender, "name", "unknown")
    celery_task_failures_total.labels(task_name=task_name).inc()
