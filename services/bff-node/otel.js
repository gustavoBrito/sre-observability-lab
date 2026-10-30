/*
 * OTel bootstrap - loaded via `node -r ./otel.js server.js` so SDK setup
 * happens before app code and instrumentation hooks every module.
 *
 * Env-driven, per OTel spec: OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT,
 * OTEL_TRACES_SAMPLER... So deployment decides observability config, not code.
 */
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { getNodeAutoInstrumentations } = require("@opentelemetry/auto-instrumentations-node");
const { OTLPTraceExporter } = require("@opentelemetry/exporter-trace-otlp-grpc");

// Opt out of the hot paths we exclude in the collector pipeline anyway.
const IGNORED_ROUTES = ["/healthz", "/metrics"];

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),
  instrumentations: [
    getNodeAutoInstrumentations({
      "@opentelemetry/instrumentation-http": {
        ignoreIncomingRequestHook: (req) => IGNORED_ROUTES.includes(req.url),
      },
      "@opentelemetry/instrumentation-fs": { enabled: false },
    }),
  ],
});

sdk.start();

process.on("SIGTERM", () => {
  sdk
    .shutdown()
    .catch((err) => console.warn("OTel shutdown error:", err))
    .finally(() => process.exit(0));
});
