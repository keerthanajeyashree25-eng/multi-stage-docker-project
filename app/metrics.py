"""Prometheus metrics for the Flask application."""

import os
from time import perf_counter, time

from flask import Response, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
    multiprocess,
)

HTTP_REQUESTS = Counter(
    "http_requests",
    "Total HTTP requests handled by the application.",
    ("method", "endpoint", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "endpoint"),
)
HTTP_ERRORS = Counter(
    "http_errors",
    "Total HTTP responses with a 4xx or 5xx status.",
)
APPLICATION_HEALTH = Gauge(
    "application_health",
    "1 if the most recent health check succeeded, otherwise 0.",
    multiprocess_mode="livemax",
)
APPLICATION_START_TIME = Gauge(
    "application_start_time_seconds",
    "Unix timestamp when the oldest live application worker started.",
    multiprocess_mode="livemin",
)
APPLICATION_START_TIME.set(time())

if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
    METRICS_REGISTRY = CollectorRegistry()
    multiprocess.MultiProcessCollector(METRICS_REGISTRY)
else:
    METRICS_REGISTRY = REGISTRY


def register_metrics(application):
    @application.before_request
    def _start_request_timer():
        if request.endpoint != "prometheus_metrics":
            g.prometheus_request_started_at = perf_counter()

    @application.after_request
    def _record_request(response):
        if request.endpoint == "prometheus_metrics":
            return response

        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        method = request.method
        status = str(response.status_code)
        HTTP_REQUESTS.labels(method, endpoint, status).inc()
        started_at = getattr(g, "prometheus_request_started_at", None)
        if started_at is not None:
            HTTP_REQUEST_DURATION.labels(method, endpoint).observe(
                perf_counter() - started_at
            )
        if response.status_code >= 400:
                HTTP_ERRORS.inc()
        if request.endpoint == "main.health":
            APPLICATION_HEALTH.set(1 if response.status_code < 400 else 0)
        return response

    @application.get("/metrics", endpoint="prometheus_metrics")
    def prometheus_metrics():
        return Response(
            generate_latest(METRICS_REGISTRY),
            content_type=CONTENT_TYPE_LATEST,
        )
