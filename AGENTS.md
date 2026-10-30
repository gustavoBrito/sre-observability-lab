# AGENTS.md — Read before doing ANY changes to this repo

This file is the prerequisite brief for AI agents (OpenCode, Codex, Claude,
Copilot) and humans alike. Something not following it = change rejected.

## Project intent

**Observability showcase** mirroring a production-grade architecture:
Node BFF fronting Python and Go services with OTel end-to-end, SLOs and
burn-rate alerts. Quality bar: "could I defend this in a live production
incident review?"

## Prerequisites (order matters)

1. **Read first (mandatory):**
   - `docs/architecture.md` — the structure/dependency contract;
   - `docs/adr/` — architecture decisions ADRs (structural change? write
     a new ADR into it using `0000-template.md`);
   - `docs/testing-policy.md` — the "how we measure quality" contract;
   - `docs/slo.md` + any relevant runbook in `docs/runbooks/`.
2. **Definition of Done (gates, not suggestions):**
   - [ ] `yamllint -c .yamllint.yml .` passes
   - [ ] `ruff check services/pricing-py` passes
   - [ ] **Test coverage >= 90%** on all touched languages
         (enforced in CI; see testing-policy for exact commands)
   - [ ] Security/supply-chain audit job green (npm audit / pip-audit /
         govulncheck) — new deps must not add known-high vulnerabilities
   - [ ] Structural change => new ADR
   - [ ] New alert => runbook link added
3. **Local runs that must pass before pushing:**
   - `docker compose config -q`
   - each language test suite for files you touched

## Hard conventions

- **Config over UI**: dashboards, datasources, scrape/collector configs are
  files. Never "click it in Grafana".
- **Low-cardinality labels only** (`endpoint`, `method`, `status_code`).
- **Metric names are a contract**: `bff_http_requests_total`,
  `pricing_http_requests_total`, `inventory_http_requests_total` (+ matching
  `*_duration_seconds` histograms) are referenced by
  `prometheus/rules/slo-alerts.yml` and every service under `services/`.
  Change all sides together, in the same commit.
- **Every alert ships with a runbook** in `docs/runbooks/`; add
  `runbook_url` annotations.
- **Injected randomness goes through injection seams** (see
  `services/inventory-go/main.go` `nextRandom`, monkeypatched random in
  python tests). Do not "clean up" the failure injection — it exists so
  that alerts and dashboards show real behavior.
- **Outbound HTTP always via instrumented clients** (otelhttp / httpx
  instrumentation / node auto-instrumentation). Never hand-roll
  `traceparent` headers.
- Python: 4-space, type hinted public functions, ruff clean.
- Go: run `go vet`; comment on exported symbols.
- Node: CommonJS, `express`, no new frameworks without an ADR.

## Security

- Never commit secrets/tokens. Config via env at deployment.
- New dependencies require: pinned version + passing the audit gate.
- Telemetry backplane (collector, Tempo, Loki, Prometheus) has no published
  ports; only Grafana view-only + the BFF API are exposed (see
  `.github/SECURITY.md`).
