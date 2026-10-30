# ADR 0004: governed agent army - roles, permission matrix, human in loop

**Status:** accepted
**Date:** 2026-10

## Context

The owner's operating model runs on AI agents. The dream state: a prompt like
"add a Jira integration to project X" is decomposed and executed by
specialized agents (architecture, security, integration, review, telemetry,
rollout...). The danger in this model is well known: agents that "decide
alone" drift, invent, and disable gates to get green.

What already exists in this repo makes the army governable: `AGENTS.md` (DoD
as machine-checkable gates), ADRs, testing policy, metrics contract, runbooks,
and CI that enforces coverage/audits. The instrument missing was the roster
itself: named agent profiles, scoped, that OpenCode can load natively.

## Decision

1. **Roster lives in the repo** (`.opencode/agents/*.md`, OpenCode V2 format):
   versioned, reviewable, diffable - the constitution travels with the code.
   - `commander` (primary): the ONLY primary agent; decomposes prompts,
     launches subagents, integrates results, runs local gates, NEVER pushes
     without owner confirmation.
   - Subagents: `architect`, `integrator`, `security`, `reviewer`,
     `telemetry`, `rollout`, `chaos`, `triage`, `curator`.
2. **Permission matrix per agent** (frontmatter): read-only by default;
   write scopes are per responsibility (e.g., telemetry writes only
   `prometheus/**`, `grafana/**`, `**/observability/**`, docs of its domain;
   architect writes only `docs/**`; rollout writes only rollouts + changelog
   + handoff). `git push` is denied at every subagent.
3. **Human-in-the-loop at merge**: agents produce work; the owner confirms
   push/merge. Gates (CI) remain the objective truth - no agent vouches for
   "green", CI does.
4. **Commander allowlist**: the `subagent` permission explicitly enumerates
   the roster - no agent spawns arbitrary children.
5. **Distribution**: with the ADR-0003 polyrepo split, the SAME roster files
   are copied into each repo (documented as part of the split checklist) so
   every repo inherits the army automatically.

## Alternatives considered

- **One generalist agent** (does everything): cheaper, but no separation of
  duties - the reviewer reviewing its own code is exactly what this model
  exists to avoid. Rejected.
- **External orchestrator** (n8n workflow + OpenCode SDK/API): powerful for
  enterprise triggers (ticket arrival -> commander session), noted as the
  future phase; the in-repo roster is the foundation either way.
- **Free-for-all team agents** (no permission matrix): fast until it deletes
  the seams or "fixes" the failure injection. Rejected by AGENTS.md hard
  conventions (seams are theirs to exercise, chaos agent's, never remove).

## Consequences

- Agents inherit project instructions automatically (AGENTS.md etc.), so the
  roster files stay SHORT - constitution is referenced, not copied.
- Every task produces both the artifact AND the continuity record
  (CHANGELOG/HANDOFF updates) - commander enforces as DoD.
- New roles are added the same way: an `.md` file + commander allowlist line
  + a line in `docs/agent-army.md`. Nothing else.
- The army's blind spot remains runtime verification (e.g., real compose
  runs); chaos agent works with seams + loadgen, and Docker Desktop
  validation stays a milestone in `docs/handoff/HANDOFF.md`.
