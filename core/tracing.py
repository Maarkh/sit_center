# core/tracing.py
"""OpenTelemetry distributed tracing setup.

Enabled via OTEL_ENABLED=true. Exports to OTLP collector at OTEL_EXPORTER_OTLP_ENDPOINT.
If OTEL is not enabled or dependencies are missing, tracing is a no-op.
"""
import os
from config import logger


def setup_tracing(app=None):
    """Configure OpenTelemetry for FastAPI if enabled."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED != true)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Install: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-grpc "
            "opentelemetry-instrumentation-fastapi "
            "opentelemetry-instrumentation-sqlalchemy "
            "opentelemetry-instrumentation-redis "
            "opentelemetry-instrumentation-requests"
        )
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "sit-center-api")
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy
    try:
        from core.database import get_engine
        engine = get_engine()
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine if hasattr(engine, 'sync_engine') else engine)
    except Exception as e:
        logger.debug(f"SQLAlchemy instrumentation skipped: {e}")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Redis instrumentation skipped: {e}")

    # Instrument outbound HTTP (requests library — i-doit, Telegram, etc.)
    try:
        RequestsInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Requests instrumentation skipped: {e}")

    logger.info(f"OpenTelemetry tracing enabled: service={service_name}, endpoint={endpoint}")
