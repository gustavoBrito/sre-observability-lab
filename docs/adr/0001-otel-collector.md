# ADR 0001: telemetry pipeline - one collector, stable metric schema

**Status:** accepted
**Date:** 2026-10
**Context:** need to collect traces, logs and metrics from services written
in three languages (Node, Python, Go) with four backends (Prometheus, Loki,
Tempo, Grafana).

## Decision

1. **Traces and logs** flow through a single OpenTelemetry collector that
   enriches, filters (health/metrics spans), batches and exports OTLP to
   Tempo and Loki.
2. **SLO-grade metrics** (`*_http_requests_total`, `*_http_request_duration_seconds`)
   are exposed directly by the services on dedicated ports, scraped by
   Prometheus.

## Alternatives considered

- **All signals via collector** (OTel metrics pushed to prometheus remote
  write): single entry point is elegant, but instrumentation-library metric
  naming pivots between OTel versions, and a silent rename would break
  burn-rate alerting. Rejected for anything in SLO math's blast radius.
- **Direct app -> all backends** (no collector): every service needs
  vendor-specific exporters; changing observability tooling rewrites all
  services. Rejected.
- **Agent-based log shipping** (Loki loki-container plugin): depends on host
  integration semantics which do not match Docker-Desktop-on-Windows and
  Kubernetes-based storage assumptions. Rejected here; note that in
  production environments, log shipping via daemonset is fine and this
  constraint is lab-specific.

## Consequences

- The collector becomes a hot component - single point of enrichment; it is
  stateless and horizontally scalable in production. We accept the blast
  radius documented (dead pipeline gets noisy: the `debug` exporter is left
  on intentionally so a trace/export error surfaces locally in dev builds).
- The "dual-head" metric contract is easy to test: a CI check validates
  alert rules and service metric names in tandem (see AGENTS.md).
