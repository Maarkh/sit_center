# celery_app.py
from __future__ import annotations
from celery import Celery
from urllib.parse import quote_plus
from celery.signals import worker_shutting_down


def make_celery(app_name=__name__):
    from config import settings

    if settings.REDIS_URL:
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
        beat_schedule=get_beat_schedule(),
        task_routes={
            'core.ml_tasks.*': {'queue': 'ml'},
        },
    )
    return celery

def get_beat_schedule():
    from celeryconfig import beat_schedule
    return beat_schedule

celery_app = make_celery()

import core.celery_metrics  # noqa: F401, E402 — register Celery signal handlers
import core.dss_tasks  # noqa: F401, E402 — register DSS beat tasks (default queue)

@worker_shutting_down.connect
def worker_shutting_down_handler(sig, how, exitcode, **kwargs):
    from config import logger
    logger.info(f"Worker shutting down (sig={sig}, how={how})")

