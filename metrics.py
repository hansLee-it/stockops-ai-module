"""Prometheus metrics for the StockOps AI Forecasting Service.

Architecture: metrics use the Prometheus **pull** model — a ``/metrics`` endpoint
scraped by Prometheus — mirroring the api-server's ``/actuator/prometheus``. This
is the metrics half of the documented observability split: Prometheus for metrics,
OpenTelemetry/OTLP for traces (see ``telemetry.py``). No OTel Collector is involved.

Unlike tracing (opt-in via ``OTEL_EXPORTER_OTLP_ENDPOINT``), ``/metrics`` is exposed
unconditionally so a scraper can reach it with zero extra config, exactly like
Spring Boot actuator.

Single-process note: these counters live on the default (single-process)
``prometheus_client`` registry. The service runs under a single uvicorn worker
(see ``Dockerfile``), so that is correct. If it is ever switched to gunicorn with
multiple workers, enable ``prometheus_client`` multiprocess mode
(``PROMETHEUS_MULTIPROC_DIR``) or each worker will export only its own partial
counters.
"""

from __future__ import annotations

import logging

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# --- Custom business metrics (registered on the default registry) ---
# Labels are kept deliberately low-cardinality (no product_id) to stay
# Prometheus-friendly; per-product detail belongs in traces, not metrics.

FORECAST_REQUESTS = Counter(
    "ai_forecast_requests_total",
    "Demand-forecast computations, labelled by outcome.",
    ["outcome"],  # success | error
)

FORECAST_DURATION = Histogram(
    "ai_forecast_duration_seconds",
    "End-to-end forecast computation latency in seconds.",
)

MODEL_CACHE_EVENTS = Counter(
    "ai_model_cache_events_total",
    "Prophet model-cache lookups, labelled by result.",
    ["result"],  # hit | miss
)

MODEL_TRAIN_DURATION = Histogram(
    "ai_model_train_duration_seconds",
    "Prophet model fit() duration in seconds (cache misses only).",
)

EVALUATION_MAPE = Histogram(
    "ai_evaluation_mape_percent",
    "Distribution of model-evaluation MAPE (%) across runs.",
    buckets=(5, 10, 15, 20, 30, 50, 75, 100),
)


def setup_metrics(app) -> None:
    """Expose Prometheus metrics for the FastAPI app via a pull ``/metrics`` endpoint.

    Adds default HTTP-server metrics (request count, latency, in-progress) using
    ``prometheus-fastapi-instrumentator`` — the rough equivalent of Micrometer's
    ``http.server.requests`` — then mounts ``/metrics``. The custom business
    metrics defined above share the same default registry, so they appear on the
    same endpoint. Always-on (no env gate), mirroring actuator.
    """
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
    except ImportError:
        logger.warning(
            "prometheus-fastapi-instrumentator not installed; HTTP metrics disabled "
            "(custom /metrics still served if mounted elsewhere).",
            exc_info=True,
        )
        return

    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    logger.info("Prometheus metrics enabled at /metrics (pull model).")
