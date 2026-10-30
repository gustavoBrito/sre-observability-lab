/* Contract metrics (same names as Prometheus rules) + RED middleware. */

const { register, Counter, Histogram, collectDefaultMetrics } = require("prom-client");

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

/** Middleware keeping RED metrics on every route automatically. */
function redMiddleware(req, res, next) {
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
}

module.exports = { reqTotal, reqLatency, redMiddleware, register };
