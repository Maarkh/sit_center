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
        # requeued if the worker dies mid-task. The partial-unique indexes
        # (ux_deviations_active_fp / ux_predalerts_active_fp) and ON CONFLICT upserts
        # make re-runs safe against *duplicates*. Caveat (not full idempotency): the
        # per-tenant evaluation loop commits per indicator and the chronicle/periods
        # counters are additive, so a worker lost mid-loop could re-process already-
        # committed indicators and inflate those counters. soft_time_limit (see the
        # task decorators) makes the common time-out path unwind gracefully instead of
        # SIGKILL mid-loop; the residual (OOM/evict) is a rare, bounded over-count.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        beat_schedule=get_beat_schedule(),
        task_routes={
            'core.ml_tasks.*': {'queue': 'ml'},
        },
    )
    # RedBeat (the Redis-backed beat scheduler used in K8s/compose) reads
    # redbeat_redis_url, defaulting to broker_url. It speaks plain redis:// only —
    # NOT Celery's sentinel:// scheme — so under Sentinel we must resolve the current
    # master to a concrete redis:// URL, or RedBeat fails to start (beat dies in the
    # exact HA mode Sentinel provides). On failover the beat liveness probe restarts
    # the pod, which re-resolves the new master.
    if sentinel_opts:
        celery.conf.broker_transport_options = sentinel_opts
        celery.conf.result_backend_transport_options = sentinel_opts
        celery.conf.redbeat_redis_url = _resolve_redbeat_url(settings, nodes)
    else:
        celery.conf.redbeat_redis_url = redis_url
    return celery


def _resolve_redbeat_url(settings, sentinel_nodes):
    """Concrete redis:// URL for RedBeat under Sentinel. Honours an explicit
    REDBEAT_REDIS_URL override; otherwise discovers the master via Sentinel. Returns
    None on failure (RedBeat then falls back to broker_url and logs)."""
    import os
    import logging
    log = logging.getLogger("celery")
    override = os.environ.get("REDBEAT_REDIS_URL")
    if override:
        return override
    try:
        from redis.sentinel import Sentinel
        hostports = []
        for n in sentinel_nodes:
            host, _, port = n.partition(":")
            hostports.append((host, int(port or 26379)))
        skwargs = {"password": settings.REDIS_SENTINEL_PASSWORD} if settings.REDIS_SENTINEL_PASSWORD else {}
        sentinel = Sentinel(hostports, sentinel_kwargs=skwargs,
                            password=settings.REDIS_PASSWORD or None)
        mhost, mport = sentinel.discover_master(settings.REDIS_MASTER_NAME)
        auth = f":{quote_plus(settings.REDIS_PASSWORD)}@" if settings.REDIS_PASSWORD else ""
        return f"redis://{auth}{mhost}:{mport}/{settings.REDIS_DB}"
    except Exception as e:
        log.warning("RedBeat master discovery under Sentinel failed (%s); set REDBEAT_REDIS_URL "
                    "to a concrete redis:// master URL", e)
        return None

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
    # Close the Telegram aiohttp session the worker may hold. This used to be wired to a
    # process-wide SIGTERM handler at import (core/notifications), which clobbered
    # Celery's graceful drain — now it runs inside Celery's own shutdown path.
    try:
        from telegram_bot import close_telegram_session_sync
        close_telegram_session_sync()
    except Exception:
        logger.debug("Telegram session close skipped")

