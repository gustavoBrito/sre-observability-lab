# Service Level Objectives - BFF (user-facing edge)

## Why the BFF is the SLO surface

Users experience the product through the Node BFF. Internal services have
their own dashboards (dependency-grade), but the *commitment* is measured at
the edge. Dependency SLOs derive from edge SLOs, never the other way around.

## Objectives (30-day windows)

| SLI | Definition (PromQL source) | SLO | Budget (30d) |
|---|---|---|---|
| Availability | fraction of HTTP responses with `status_code` < 500 | 99.9% | 43m 50s |
| Latency | fraction of responses served < 500ms | 99% | 7h 15m |

## Error budget policy

When budget burn crosses thresholds, these actions are pre-agreed:

- **> 50% budget burned** (alert `SLOBFFAvailabilityBurnRateSlow`): risky
  changes to this service are gated; review of contributing dependencies.
- **100% burned**: feature releases freeze for this service; team response
  is focused on quality/perf work until budget recovered.
- Overrides only by the Tech Lead, with the decision written in the incident
  channel.

## Multi-window burn-rate alerts (Google SRE Workbook approach)

| Alert | Windows | Burn rate | Route |
|---|---|---|---|
| `SLOBFFAvailabilityBurnRateFast` | 5m + 1h | > 14.4x | page |
| `SLOBFFAvailabilityBurnRateSlow` | 30m + 6h | > 6x | ticket |
| `SLOBFFLatencyBurnRateFast` | 5m + 1h | > 14.4x | page |

Rationale: short+long window pairs cut the noise of single-window alerting
while keeping the 2 paged alerts per 1M requests target. Every page carries a
`runbook` annotation in the Alert rules.
