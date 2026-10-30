# Architecture - how this portfolio is structured, and why

This document is the **contract** every contributor (human or AI agent) must
follow. Structural changes require a new ADR in `docs/adr/`.

## Topology

```
client/user -> BFF (b, Node)  ->  pricing (p, Python) -> inventory (i, Go)
                  edge layer          service layer        domain layer
```

### Dependency rules (hard, reviewable)

1. **Direction of calls**: `b -> p -> i` only. A deeper layer NEVER calls a
   shallower one, and services never skip layers (i must not know b exists).
2. **Optional dependency**: every dependency call needs a timeout, an error
   path that degrades locally (no cascading retries), and propagation via
   the instrumented client (never manual headers).
3. **Single write surface**: everything you can do in a tool UI lives as
   code: dashboards, datasources, scrape configs, alert rules.
4. **BFF responsibilities**: aggregation + HTTP mapping. NO business logic,
   no persistence, no direct DB access.

## Observability invariants

- **SLOs measured at the edge** (BFF). Dependencies emit metrics and are
  graded, but the *commitment* lives at the boundary the user feels.
- **Metric names are a cross-language contract** between the three services
  (`bff_http_requests_total`, `pricing_http_requests_total`,
  `inventory_http_requests_total` + matching `*_duration_seconds`
  histograms) and `prometheus/rules/slo-alerts.yml`.
- **Low-cardinality labels only.**
- **An alert without a runbook is a bug.**

## Security invariants

- No secrets in code. Config comes from env at deployment time.
- Telemetry endpoints (collector, Tempo, Loki, Prometheus) are never exposed
  beyond the internal network; only Grafana (view-only anonymous) and the
  edge API get published ports.
- Every third-party dep comes from a pinned version in a lock/require file,
  and CI audits supply chain on global scale (npm audit / pip-audit /
  govulncheck).

## Agent governance (prerequisites, not suggestions)

AI agents (Codex, Claude, OpenCode) MUST read `AGENTS.md` before altering
code, and the Definition of Done gates there are enforced:

- architecture compliance (this document + ADRs),
- security checks in CI (dependency/supply-chain audits),
- code quality: tests with coverage threshold **>= 90%** per language see
  `docs/testing-policy.md`,
- observability contract (metric names + runbooks),
- a new ADR for any structural change.
