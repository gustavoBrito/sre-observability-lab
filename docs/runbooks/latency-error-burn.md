# Runbook: high error-rate burn (BFF availability SLO)

**Alert:** `SLOBFFAvailabilityBurnRateFast` / `SLOBFFAvailabilityBurnRateSlow`
**Severity:** page (fast) / ticket (slow)
**Expected triage time:** 5 min

## 1. Confirm it is user-facing

- Open dashboard `Service Overview - RED + SLO` and check the Traffic panel
  for the `500+` series vs. the 2xx volume; confirm no scrape gap
  (see Prometheus target page).

## 2. Localize the failure

Use the dependency panels (pricing / inventory) to see which hop is failing
*first*:

- pricing error ratio high, inventory clean -> problem is between BFF and
  pricing (network, pricing's outlier config, persistence read).
- inventory failing as well -> suspect shared cause (彼此 payment gateway?).

## 3. Get the trace evidence (key step)

- Go to Tempo: pick a recent failed BFF span via exemplar link,
  or from Loki error log line -> `trace_id` link.
- In the trace waterfall, identify the failing span (exactly one service
  "breaks" first; verify where the exception was logged in the log panel).

## 4. Typical causes and fixes

| Signal | Likely cause | Action |
|---|---|---|
| inventory 5xx bursts | slow queries / DB pool exhaustion | scale inventory, check pool saturation panel (roadmap) |
| latency + errors at pricing | thread/memory throttling | inspect resource events, restart if required |
| all services fine, BFF rising | component bug at BFF | rollback last deploy of bff |

## 5. Escalate when

- No runbook entry matched, or
- budget burn exceeds ~30% in 1h, or
- 2 pages in 1h — page the primary's owner, not the service.

## 6. Post-incident

Any page triggered by an alert without a corresponding code/root-cause fix
dating more than 30 days old must update this runbook with what was missed.
