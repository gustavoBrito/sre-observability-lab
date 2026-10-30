# ADR 0002: topology - one repo (monorepo), three independent deploys,
# observability injected

**Status:** accepted
**Date:** 2026-10

## Context

A recurring question: "is this a monolith? Do we need to redeploy the whole
project whenever one component changes? Can we only run it with Docker? Could
we go microservices - each component its own project/spec, deployed
individually, with observability injected into the apps instead of inlined?"

Forces at play: portfolio clarity (one repo to review), the cross-language
**metric-name contract** (`bff/pricing/inventory_http_requests_total` must
change on all sides together per AGENTS.md), per-service deploy granularity,
and the teaching goal: show the *right* separation, not buzzwords.

## Decision

1. **This IS microservices; the repo is a monorepo - different things.**
   Three separately-built, separately-deployable runtimes exist today:
   separate processes, ports, Dockerfiles (one image per service), CI jobs,
   language toolchains, and **zero shared code**. No shared library, no
   shared release train.
2. **Deploy granularity is per-service NOW.** `docker compose up -d --build
   inventory` rebuilds/restarts exactly one image; the rest of the stack
   keeps running untouched. Images are immutable once pushed.
3. **Docker/compose is the lab *runtime*, not the architecture.** Services
   depend on env vars + OTLP endpoints, never on compose. The same images
   deploy unchanged to Kubernetes/Helm, ECS, Cloud Run, or VMs.
4. **Observability as injection, not inline lib-coupling.** Apps only speak
   OTLP over env-configured endpoints (`OTEL_EXPORTER_OTLP_ENDPOINT`,
   `OTEL_SERVICE_NAME`). Evolution path (phase 2): collector **agent as a
   sidecar/daemonset** - apps emit to `localhost:4317/4318` and the agent is
   attached per-pod by the platform, reducing app-side telemetry code to
   (near) zero. Tracing propagation stays auto-instrumented.
5. **Phase 2 roadmap (accepted direction, not yet built):** per-service Helm
   charts, per-service pipelines with path filters (monorepo already splits
   by language/job; polyrepo remains possible later), contract-test package
   for metric names when/if the repo splits.

## Alternatives considered

- **Polyrepo today ("one repo per caixinha"):** visually satisfying, but the
  metric contract must be validated across all services in one place; three
  repos multiply review latency and drift on a 3-service lab. Rejected for
  now; documented as mechanical migration (see #5) when the team/domain count
  justifies it.
- **Shared "platform library"** (one instrumentation package per language,
  version-locked against all services): couples app releases to telemetry
  releases, exactly the coupling the collector/sidecar pattern removes.
  Rejected per ADR-0001 direction.
- **Service mesh now (Istio/Linkerd):** mTLS, traffic policy, and retries
  without a real user for them in this lab. Deferred to phase 3; the BFF
  already owns timeout/retry semantics at its edge.

## Consequences

- Easier: demonstrate per-component rebuild/redeploy; the story "change one
  .go file -> one image rebuilt, stack still live" is real today.
- Easier: backend swap (e.g., Tempo -> Jaeger) touches only the collector
  and/or an overlay, never service code.
- Harder/accepted: while monorepo, the metric-name contract test stays
  hosted here (one CI run sees all sides). If we split repos, that test
  becomes a standalone contract package - a listed migration step.
- regardless of the repo layout: **one process per box, one image per
  service, independent deploy** is already true; compose only wires the
  network.
