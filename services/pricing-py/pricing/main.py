"""Bootstrap: FastAPI app assembly + OTel + metrics middleware.

Wiring only (see AGENTS.md). Business lives in pricing/services/; HTTP edges
in pricing/routers/; gateways in pricing/repositories/.
"""

import time
from fastapi import FastAPI
from prometheus_client import start_http_server
import uvicorn

from pricing.observability import telemetry
from pricing.observability.metrics import LATENCY, REQUESTS
from pricing.routers import price

# OTel (traces + logs) configured BEFORE instrumenting the app
telemetry.configure()

app = FastAPI(title="pricing-py")
app.include_router(price.router)


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


telemetry.instrument_http(app)  # tracer middleware (thin wrapper)

if __name__ == "__main__":
    start_http_server(9002)
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
