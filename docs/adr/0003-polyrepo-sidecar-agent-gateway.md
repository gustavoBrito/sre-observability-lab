# ADR 0003: polyrepo split + OTel agent sidecar (agent->gateway)

**Status:** proposed (pending owner approval)
**Date:** 2026-10

## Context

ADR-0002 documented the destination architecture: per-service deploys,
observability as injection (sidecar), and a *documented migration path* for
splitting the monorepo. Two developments make the transition timely:

1. The owner works daily on Mercado Livre's **Fury platform** (Kubernetes
   application platform: one repo + pipeline per microservice, the platform
   injects infrastructure). A lab that mirrors this model is directly
   transferable as professional argument.
2. The strongest asset of the lab is the cross-language **metric-name
   contract**; splitting repos naively would spread that contract across
   reviews and let it drift.

## Decision (proposed)

1. **Contract first, split second.** Before touching repo layout, extract
   `telemetry-contracts`: metric names + label set + a runnable contract
   test, published as a package consumed by every service's CI. All services
   MUST pass contract validation against the profile of their own names.
2. **Split the lab into repositories:**
   - `telemetry-contracts` (the shared product: metric names, contract
     tests, semantic references)
   - `obs-lab-bff` (Node BFF)
   - `obs-lab-pricing` (Python pricing)
   - `obs-lab-inventory` (Go inventory)
   - `obs-lab-stack` (compose/Helm, dashboards-as-code, gateway collector,
     loadgen)
3. **Sidecar via two-tier OTel (agent -> gateway)**, the standard OTel
   deployment pattern:
   - per service, an `otel-agent` (small collector) runs as a SIDEcar:
     compose `network_mode: "service: app"` replicates pod-localhost
     semantics without k8s; apps emit to `localhost:4317/4318`;
   - the agent does only local telemetry hygiene (memory limiter, batching);
   - enrichment/sampling/fan-out stays in the central `gateway` collector
     (ADR-0001 stays valid: it keeps the single point of enrichment).
   - On a real k8s/Fury-like platform, the agent is attached per-pod by the
     platform - apps carry no telemetry deployment knowledge.
4. **Repo shape mirrors Fury conventions** (pipeline per repo, identical
   validate/test/security jobs, dockerfile per app image) so the story
   "same patterns as work" holds; naming/details documented here.
5. Precedent repos: the monorepo stays as archive/history; `AGENTS.md`
   lives on in `obs-lab-stack` (platform governance) + a slim per-repo
   DOCS pointer (kept up to date in each repo).

## Alternatives considered

- **Stay monorepo** (ADR-0002 status quo): cheaper, but leaves the lab
  unable to demonstrate the team/ownership split that per-repo pipelines
  imply - and less directly transferable to the owner's daily platform.
- **Polyrepo without a contract artifact** (naive split): keeps metric
  names reviewed across four repos; the drift risk is the reason the split
  was parked. Rejected as "split without contract extraction."
- **Full service mesh instead of sidecars** (Istio etc.): still rejected;
  two-tier OTel gives injection semantics without mesh ops burden.

## Consequences

- Easier: per-repo CI green badges, truly independent release cadences, and
  a contract artifact that is *tested everywhere, owned once* - the
  argument becomes demonstrable ("change a metric name without updating all
  sides and your CI blocks the PR").
- Easier: sidecar demo works TODAY in compose (`network_mode` share), and
  the same agent/gateway topology maps 1:1 onto k8s pods later.
- Harder/accepted: five repos need cross-repo linking (README hub in
  `obs-lab-stack`); updates to the contract go through one PR there,
  and services bump the pinned version in their CI (supply-chain style).
- Migration checklist lives with the phase-2 roadmap debt in HANDOFF; the
  split is mechanical ONLY after step 1.
