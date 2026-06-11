# core/tracing.py
"""OpenTelemetry distributed tracing setup.

Enabled via OTEL_ENABLED=true. Exports to OTLP collector at OTEL_EXPORTER_OTLP_ENDPOINT.
If OTEL is not enabled or dependencies are missing, tracing is a no-op.

Two entry points:
  * setup_tracing(app)      — the FastAPI process (web).
  * setup_celery_tracing()  — Celery worker/beat processes (call per worker process).
Both share one OTLP exporter/provider and add the cross-cutting instrumentations
(SQLAlchemy, Redis, outbound HTTP, Kafka) so a request → task → DB/Kafka hop is one
connected trace.
"""
import os
from config import logger

# Guards: a TracerProvider is global+process-wide, and each Instrumentor patches a
# library once. Re-running (e.g. provider already set, worker re-fork) would warn or
# double-instrument, so make both idempotent.
_provider_ready = False


def _otel_enabled() -> bool:
    return os.getenv("OTEL_ENABLED", "false").lower() == "true"


def _ensure_provider(default_service: str) -> bool:
    """Set the global OTLP TracerProvider once. Returns True if tracing is live."""
    global _provider_ready
    if _provider_ready:
        return True
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    except ImportError:
        logger.warning("OpenTelemetry SDK not installed — tracing disabled")
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", default_service)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
    trace.set_tracer_provider(provider)
    _provider_ready = True
    logger.info(f"OpenTelemetry provider ready: service={service_name}, endpoint={endpoint}")
    return True


def _instrument_sqlalchemy():
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from core.database import get_engine
        engine = get_engine()
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine if hasattr(engine, "sync_engine") else engine
        )
    except Exception as e:
        logger.debug(f"SQLAlchemy instrumentation skipped: {e}")


def _instrument_redis():
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Redis instrumentation skipped: {e}")


def _instrument_requests():
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Requests instrumentation skipped: {e}")


def _instrument_kafka():
    """Trace kafka-python produce/consume (alert fan-out, metric ingestion)."""
    try:
        from opentelemetry.instrumentation.kafka import KafkaInstrumentor
        KafkaInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Kafka instrumentation skipped: {e}")


def setup_tracing(app=None):
    """Configure OpenTelemetry for the FastAPI (web) process if enabled."""
    if not _otel_enabled():
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED != true)")
        return
    if not _ensure_provider("sit-center-api"):
        return

    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception as e:
            logger.debug(f"FastAPI instrumentation skipped: {e}")

    _instrument_sqlalchemy()
    _instrument_redis()
    _instrument_requests()
    _instrument_kafka()
    logger.info("OpenTelemetry tracing enabled (web)")


def setup_celery_tracing():
    """Configure OpenTelemetry for a Celery worker/beat process if enabled.

    Call once per worker process (wired to the worker_process_init signal) so each
    pre-forked process gets its own exporter. Instruments Celery task spans plus the
    same SQLAlchemy/Redis/HTTP/Kafka libraries the tasks touch — a published task and
    its execution become parent/child spans, and DB/Kafka work nests under the task.
    """
    if not _otel_enabled():
        return
    if not _ensure_provider("sit-center-worker"):
        return

    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Celery instrumentation skipped: {e}")

    _instrument_sqlalchemy()
    _instrument_redis()
    _instrument_requests()
    _instrument_kafka()
    logger.info("OpenTelemetry tracing enabled (celery worker)")
