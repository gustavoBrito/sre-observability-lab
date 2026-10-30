"""Pricing service (Python/FastAPI) - second hop in the distributed trace.

Chain: bff -> pricing -> inventory
Demonstrates: OTel SDK wiring, httpx context propagation, OTLP log export,
and Prometheus exposition. Error injection makes burn-rate alerts fire
realistically.
"""

import asyncio
import json
import logging
import os
import random
import time

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, start_http_server

# --- OpenTelemetry setup (traces + logs) ------------------------------------
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://inventory:8003")
PORT_METRICS = int(os.environ.get("PORT_METRICS", "9002"))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("pricing")

# Resource picks up OTEL_SERVICE_NAME and friends from the environment:
# deployment config drives telemetry identity, not hardcoded names.
resource = Resource.create()

# Traces
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(trace_provider)

# Logs exported as OTLP (so Loki gets them without agents shelling stdout)
log_provider = LoggerProvider(resource=resource)
log_provider.add_processor(BatchLogRecordProcessor(OTLPLogExporter()))
logging.getLogger().addHandler(
    LoggingHandler(level=logging.INFO, logger_provider=log_provider)
)
LoggingInstrumentor().instrument(set_logging_format=True)

# Outbound propagation: httpx calls carry traceparent automatically
HTTPXClientInstrumentor().instrument()

# --- First-class metrics for SLO math ---------------------------------------
# Metric names here are a contract with prometheus/rules/slo-alerts.yml
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

app = FastAPI(title="pricing-py")
_http = httpx.AsyncClient(timeout=3.0)


@app.middleware("http")
async def track_metrics(request, call_next):
    if request.url.path in ("/healthz", "/metrics"):
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    REQUESTS.labels(
        request.url.path, request.method, str(response.status_code)
    ).inc()
    LATENCY.labels(request.url.path).observe(time.perf_counter() - start)
    return response


@app.get("/price")
async def price(sku: str = "SKU-42"):
    """Pricing endpoint with injected error/latency distributions.

    ~5% hard failures, ~1% heavy-tail latency. Stable error/latency mix is
    what makes the burn-rate alerts in this repo meaningful.
    """
    await asyncio.sleep(random.uniform(0.02, 0.12))
    if random.random() < 0.05:
        log.error("persistence read failed for sku=%s", sku)
        raise HTTPException(status_code=500, detail="persistence unavailable")

    if random.random() < 0.01:
        await asyncio.sleep(random.uniform(0.8, 1.5))
        log.warning("heavy-tail latency hit on sku=%s", sku)

    resp = await _http.get(f"{INVENTORY_URL}/stock", params={"sku": sku})
    if resp.status_code != 200:
        log.error("upstream inventory returned %s", resp.status_code)
        raise HTTPException(status_code=502, detail="inventory error")

    data = resp.json()
    log.info("price computed sku=%s", json.dumps({"sku": sku, "stock": data.get("units", 0)}))
    return {"sku": sku, "price_usd": round(random.uniform(10, 500), 2), **data}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


FastAPIInstrumentor.instrument_app(app)


if __name__ == "__main__":
    start_http_server(PORT_METRICS)
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
