"""OpenTelemetry tracing setup for the StockOps AI Forecasting Service.

Phase 1 scope: distributed *traces* exported via OTLP/HTTP. Metrics are not
exported here (the api-server side keeps Prometheus for metrics).

Design notes:
- Tracing is OPT-IN via the ``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable.
  When it is unset/empty, ``setup_tracing`` is a no-op so the service starts
  cleanly with zero telemetry config — safe for public, collector-less defaults.
- ``FastAPIInstrumentor`` automatically extracts the incoming W3C ``traceparent``
  header, so spans created here join the trace started by the api-server caller.
- No endpoints, tokens, or credentials are hard-coded; everything comes from the
  standard ``OTEL_*`` environment variables.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_tracing(app) -> bool:
    """Configure OpenTelemetry tracing for the given FastAPI app.

    Returns ``True`` when tracing was enabled, ``False`` when it was skipped
    (no OTLP endpoint configured or the OTel packages are unavailable).
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set; tracing disabled.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed; tracing disabled.", exc_info=True
        )
        return False

    service_name = os.environ.get("OTEL_SERVICE_NAME", "stockops-ai-module")
    resource = Resource.create({"service.name": service_name})

    provider = TracerProvider(resource=resource)
    # OTLPSpanExporter reads OTEL_EXPORTER_OTLP_TRACES_ENDPOINT /
    # OTEL_EXPORTER_OTLP_ENDPOINT (appending /v1/traces) and OTEL_EXPORTER_OTLP_HEADERS
    # from the environment, so auth headers stay out of source code.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    # Optional: psycopg2 instrumentation adds DB query spans when available.
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        Psycopg2Instrumentor().instrument()
    except ImportError:
        logger.info("psycopg2 instrumentation not installed; skipping DB spans.")

    logger.info(
        "OpenTelemetry tracing enabled (service.name=%s, endpoint=%s).",
        service_name,
        endpoint,
    )
    return True
