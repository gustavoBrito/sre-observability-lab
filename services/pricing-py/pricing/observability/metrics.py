# Cross-cutting observability: CONTRACT metrics and telemetry wiring live
# here. This package is a LEAF - business code never imports back into it
# except through the middleware in main.py.

from prometheus_client import Counter, Histogram

# Metric names are a contract with prometheus/rules/slo-alerts.yml
REQUESTS = Counter(
    "pricing_http_requests_total",
    "HTTP requests handled by pricing",
    ["endpoint", "method", "status_code"],
)

LATENCY = Histogram(
    "pricing_http_request_duration_seconds",
    "Pricing request latency in seconds",
    ["endpoint"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
