# Component map - what each piece does, and what breaks without it

One-line role, where it lives in this repo, its traps. Read together with
docs/architecture.md (traffic contract). Ports and metric names listed here
are the operational source of truth.

## Edge / services

### bff-node (Node/Express, `:8000`, metrics `:9001`)
- **Role:** aggregation edge - the user-facing surface where SLOs live.
- **Owns:** `/api/orders` aggregation (called pricing), `/healthz`, RED
  middleware (`bff_http_requests_total`, `bff_http_request_duration_seconds`).
- **Files:** `src/` (app.js wiring, routes/orders thin, services aggregate +
  map upstream errors to {500|502}, observability/metrics.js contract).
- **ives without it:** nothing fronts the trace; no SLO surface.
- **Trap:** it must stay dumb. No DB, no queues, no business rules.

### pricing-py (FastAPI, `:8002`, metrics `:9002`)
- **Role:** service layer - business rules (quote), persistence + upstream
  inventory read.
- **Owns:** failure injection (~5% persistence, 1% heavy-tail) through
  seams (`rng01`, `tail01`), OTLP **logs** demo.
- **Files:** `pricing/{routers,services,models,repositories,observability}`.
- **Trap:** repositories own ALL outbound HTTP (hxxp), so propagation and
  timeouts have a single point of change.

### inventory-go (Go, `:8003`, metrics `:9003`)
- **Role:** domain layer deepest hop (stock read).
- **Owns:** `internal/{handlers,service,repository,models}` split with the
  bootstrap in `cmd/inventory` - the layering enables the honest coverage
  gate (bootstrap excluded by policy).
- **Files:** see `cmd/` + `internal/`.
- **Trap:** handlers must stay thin: parse -> service -> write. Nothing else.

### loadgen (Python, no own port)
- **Role:** synthetic traffic - keeps RED charts, exemplars and burn-rate
  alerts meaningful without a real client.

## Observability backplane

### OpenTelemetry Collector (`otel/opentelemetry-collector-contrib`)
- **Role:** single inbound for traces + logs; enrichment/batching/filter
  (drops `/healthz`, `/metrics` spans/logs), fan-out to Tempo and Loki.
- **Why:** apps speak OTLP to ONE endpoint; changing backend or adding
  processor (sampling) happens here, never re-touching services.
- **Trap:** it is a single-point for enrichment - stateless, scale-outs, or
  double it in prod modes.

### Prometheus `:9090`
- **Role:** scrape and storage; **recording rules + burn-rate alerting** by
  SLO (multi-window). Also the source for dashboards with exemplars.
- **Trap:** rule names and metric names are a contract with the three
  services' metrics (`prometheus/rules/slo-alerts.yml`).

### Tempo `:3200`
- **Role:** trace store; links back to logs by trace_id (Loki derived field)
  and metrics by exemplar (trace-to-metric clickthrough).
- **Trap:** single-binary config keeps local data under /var temp volume.

### Loki `:3100`
- **Role:** logs ingested natively via OTLP endpoint (no agent/stdout shell);
  low-cardinality labels (service, level) only.
- **Trap:** OTLP ingestion is fine for structured logs - raw stdout got
  shipped somewhere else; Loki labels must match labels low-cardinality.

### Grafana `:3000`
- **Role:** dashboards-as-code with datasource UIDs (`prometheus`,`loki`,
  `tempo`) and provisioning (no click-ops!). Cross-links: exemplars,
  trace-to-logs (from traced fields to Tempo search).

## CI / governance

- `validate` - yamllint, ruff, `docker compose config`.
- Language tests with coverage gates (see docs/testing-policy.md).
- `security` - pip-audit / govulncheck / npm audit; non-blocking overall with
  an issue tracked (see docs/handoff/HANDOFF.md debts).

## Scripts

- `scripts/check-go-coverage.py` - statement-weighted gate, dedupes double
  counted `-coverpkg` rows, excludes bootstrap (main.go). Used by CI.
