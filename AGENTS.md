# AGENTS.md — guidance for AI coding agents (OpenCode, Copilot, etc.)

This file is read by AI agents before they act on this repo. It keeps
contributions from Codex/Claude/OpenCode sessions consistent.

## Project intent

This is an **observability showcase** mirroring a real-world architecture:
a Node BFF fronting Python and Go services (BFF + polyglot pattern).
Quality bar: "could I defend this design in a production incident review?".

## Conventions

- **Config over UI**: dashboards, datasources, scrape/collector configs always
  live as files. Never "just click it in Grafana".
- **Low-cardinality labels only** (`endpoint`, `method`, `status_code`).
  Never IDs, timestamps, query strings or values from random distributions.
- **Metric names are a cross-language contract**:
  `bff_http_requests_total`, `pricing_http_requests_total`,
  `inventory_http_requests_total` (plus matching `*_duration_seconds`
  histograms) are referenced by `prometheus/rules/slo-alerts.yml` and
  by status recording rules in the services under `services/` — change all
  together, never just one side.
- **Every alert ships with a runbook** in `docs/runbooks/` — an alert without
  a runbook is a bug. Add a `runbook_url` annotation when creating alerts.
- **Propagated context, not hand-rolled tracing**: outbound HTTP in any
  service must go through an instrumented client (otelhttp / httpx
  instrumentation / node auto-instrumentation). Never set `traceparent`
  manually.
- Error and latency injection (`random` 5%/2%/1% branches) exists on purpose;
  do not "clean it up" — it makes alerts/dashboards show real behavior.

## Verify before finishing a task

1. `docker compose config -q` passes.
2. Dashboards reference datasource **UIDs** (`prometheus`, `loki`, `tempo`),
   never names.
3. No absolute `localhost` URLs inside container configs (docs/README only).
4. New Python code passes `ruff check`, YAML passes `yamllint -c .yamllint.yml .`.
