# Testing & Quality Policy

**Threshold: 90% coverage per language is a gate, published in CI.** Falling
below it fails the pipeline - no negotiation on priority branches.

## Principles

1. Tests target **behavior at the boundary**: HTTP handlers, injected-failure
   paths, dependency-error mapping. Not private functions.
2. Randomness is **injectable**: error/latency injection in production code
   runs through an overridable RNG seam, so tests force both paths
   deterministically (flaky coverage-walls are a design smell).
3. Coverage is reported and gated in CI on every commit; coverage regresses ->
   author fixes in the same PR.

## How coverage is computed

| Language        | Command | Notes |
|-----------------|---------|-------|
| Python (pricing)| `pytest --cov-fail-under=90` | via `pytest-cov`; OTel setup (module import) is executed as part of the import |
| Node (BFF)      | `npm test` (jest, `--coverage`) | thresholds enforced in `jest.config.js` |
| Go (inventory)  | `go test -coverprofile` then statement-weighted check | `main.go` (otel/servers bootstrap) is **excluded** from the gate: it is wiring, tested by integration, not by unit tests |

The Go exclusion is a decision recorded in ADR-0001's style: coverage gates
must be honest but not pessimal — untestable-in-unit bootstrap code dilutes
the signal. If that ever changes, adjust `scripts/check-go-coverage.py` and
this document together.

Current enforced numbers:

- statements / lines / functions >= **90%** in all three languages
- Node branch coverage tracked at **85%** this quarter, target: 90
  (failure-injection seams remain permanently covered by forced tests)

## Local quick runs

```bash
# Python
cd services/pricing-py && pytest --cov=. --cov-fail-under=90

# Node
cd services/bff-node && npm ci && npm test

# Go (coverage gate included)
cd services/inventory-go
go test ./... -coverprofile=cover.out
python3 ../..//scripts/check-go-coverage.py cover.out 90
```

## Done means

- New code has tests (equal number of happy/first-error/degraded paths).
- An injected error branch always has a forced test.
- No test relies on wall-clock sleeps other than the heavy-tail simulation.
