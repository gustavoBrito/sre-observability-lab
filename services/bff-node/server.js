"use strict";

const express = require("express");
const http = require("http");
const { register, Counter, Histogram, collectDefaultMetrics } = require("prom-client");

const PORT_HTTP = Number(process.env.PORT_HTTP || 8000);
const PORT_METRICS = Number(process.env.PORT_METRICS || 9001);
const PRICING_URL = () => process.env.PRICING_URL || "http://pricing:8002";

/**
 * First-class metrics for SLO math, with a stable schema. Names here are a
 * contract with prometheus/rules/slo-alerts.yml - change both together.
 */
collectDefaultMetrics({ register, prefix: "bff_node_" });

const reqTotal = new Counter({
  name: "bff_http_requests_total",
  help: "HTTP requests handled by the BFF",
  labelNames: ["endpoint", "method", "status_code"],
});

const reqLatency = new Histogram({
  name: "bff_http_request_duration_seconds",
  help: "BFF request latency in seconds",
  labelNames: ["endpoint"],
  buckets: [0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
});

const app = express();
app.disable("x-powered-by");

// Instrumentation middleware: record status + duration per route.
app.use((req, res, next) => {
  if (req.path === "/healthz" || req.path === "/metrics") return next();

  const t0 = process.hrtime.bigint();
  res.on("finish", () => {
    const dur = Number(process.hrtime.bigint() - t0) / 1e9;
    reqTotal.labels(req.path, req.method, String(res.statusCode)).inc();
    reqLatency.labels(req.path).observe(dur);
    console.log(
      `endpoint=${req.path} status=${res.statusCode} duration_ms=${(dur * 1000).toFixed(0)} trace_id=${req.headers["x-trace-id"] ?? "n/a"}`,
    );
  });
  return next();
});

/**
 * GET wrapper returning {status, body}. Rejects on non-2xx and network error,
 * so the route handler maps upstream failures to user-facing status codes.
 */
function get(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        const result = { status: res.statusCode, body };
        if (res.statusCode >= 400) reject(result);
        else resolve(result);
      });
    });
    req.on("error", reject);
    req.setTimeout(3000, () => req.destroy(new Error("upstream timeout")));
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

app.get("/api/orders", async (req, res) => {
  try {
    await sleep(40 + Math.random() * 80); // BFF processing overhead

    const pricing = await get(`${PRICING_URL()}/price?sku=SKU-42`);

    res.status(200).json({ order_id: "ord-" + Date.now(), price: pricing.body });
  } catch (err) {
    // ECONNREFUSED/timeout: 502 (bad gateway); upstream 5xx: propagate as 500
    console.error(`ERROR upstream request failed: ${JSON.stringify(err.message ?? err)}`);
    res.status(err.status ? 500 : 502).json({ error: "upstream_failure" });
  }
});

app.get("/healthz", (req, res) => {
  res.status(200).json({ status: "ok" });
});

module.exports = { app };

if (require.main === module) {
  // Dedicated metrics port (kept out of RED latency math)
  const metricsServer = http.createServer(async (_req, res) => {
    res.writeHead(200, { "content-type": register.contentType });
    res.end(await register.metrics());
  });
  metricsServer.listen(PORT_METRICS, () => console.log(`metrics on :${PORT_METRICS}`));

  app.listen(PORT_HTTP, () => console.log(`bff listening on :${PORT_HTTP}`));
}
