# celery_app.py
from __future__ import annotations
from celery import Celery
from urllib.parse import quote_plus
from celery.signals import worker_shutting_down, worker_process_init


def make_celery(app_name=__name__):
    from config import settings

    sentinel_opts = {}
    if settings.REDIS_SENTINELS:
        # HA broker/backend via Redis Sentinel: sentinel://...;sentinel://... with the
        # master name carried in transport options (Celery discovers the master).
        pwd = quote_plus(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ""
        nodes = [h.strip() for h in settings.REDIS_SENTINELS.split(",") if h.strip()]
        redis_url = ";".join(f"sentinel://:{pwd}@{n}" for n in nodes)
        sentinel_opts = {"master_name": settings.REDIS_MASTER_NAME}
        if settings.REDIS_SENTINEL_PASSWORD:
            sentinel_opts["sentinel_kwargs"] = {"password": settings.REDIS_SENTINEL_PASSWORD}
    elif settings.REDIS_URL:
        redis_url = settings.REDIS_URL
    else:
        pwd = quote_plus(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else ""
        redis_url = f"redis://:{pwd}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        broker_connection_retry_on_startup=True,
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        # At-least-once delivery: a task is ack'd only after it finishes, and is
        # requeued if the worker dies mid-task. DSS tasks are idempotent (unique
        # indexes / upserts / dedup keys), so re-runs are safe.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        beat_schedule=get_beat_schedule(),
        task_routes={
            'core.ml_tasks.*': {'queue': 'ml'},
        },
    )
    if sentinel_opts:
        celery.conf.broker_transport_options = sentinel_opts
        celery.conf.result_backend_transport_options = sentinel_opts
    else:
        # RedBeat (the Redis-backed beat scheduler used in K8s/compose) reads
        # redbeat_redis_url, defaulting to broker_url. Pin it explicitly for the
        # plain-Redis path so beat and the schedule store always share one Redis.
        # (Sentinel: RedBeat needs its own non-sentinel URL — left unset here.)
        celery.conf.redbeat_redis_url = redis_url
    return celery

def get_beat_schedule():
    from celeryconfig import beat_schedule
    return beat_schedule

celery_app = make_celery()

import core.celery_metrics  # noqa: F401, E402 — register Celery signal handlers
import core.dss_tasks  # noqa: F401, E402 — register DSS beat tasks (default queue)

@worker_process_init.connect
def init_worker_tracing(**kwargs):
    """Each pre-forked worker process gets its own OTel exporter (no-op unless
    OTEL_ENABLED). Spans for task publish/execute + DB/Redis/HTTP/Kafka now thread
    through the worker, joined to the web trace that enqueued the task."""
    try:
        from core.tracing import setup_celery_tracing
        setup_celery_tracing()
    except Exception as e:  # tracing must never break task startup
        from config import logger
        logger.debug(f"Celery OTel init skipped: {e}")


@worker_shutting_down.connect
def worker_shutting_down_handler(sig, how, exitcode, **kwargs):
    from config import logger
    logger.info(f"Worker shutting down (sig={sig}, how={how})")

