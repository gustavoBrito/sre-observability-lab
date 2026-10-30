# Metrics strategy - taxonomy, tags and business metrics

How we name, label and alert; includes the Datadog translation for people who
live in monitors (this README author runs most services there). Everything on
this page is enforced by the same rules hierarchy: metric SHAPE -> low-
cardinality tags -> decision-oriented tags (not raw IDs).

## 1. Metric taxonomy (3 tiers)

| Tier | Examples | Where alerts live |
|---|---|---|
| **RED (edge)** | `bff_http_requests_total`, latency histograms | burn-rate SLO alerts |
| **USE / dependency-grade** | per-service availability ratios, resource gauge (pool size...) | tickets, dashboards |
| **Business** | `orders_created_total{channel,region}`, `quote_conversion_ratio` | product + SRE KPIs, budget burn for business KPIs |

Only tier 1 gets pages. Tier 2/3 never page-directly in this lab; instead,
they drive investigation via dashboards (Datadog-style: metrics in monitors
that are connected to runbooks).

## 2. Naming and shape conventions

- Name = `<service>_<domain>_<action>[_unit]_total`:
  - `bff_http_requests_total`, `pricing_http_requests_total`
  - counters end `_total`; histograms end `_seconds` / bytes explicitly.
- Unit suffixes (seconds/bytes) are mandatory where they exist.
- Shape first, then Grafana/Datadog: the same series streams into both when
  the OTel Pipelines are extended; in Datadog this shows up as a metric with
  the SAME name and tags -> dashboards as code in both worlds are one truth.

## 3. Tag taxonomy (ranks of utility)

**Universal (always present):**
- `service`, `env` (prod/staging/lab), `region/cluster`, `team`

**Decision-oriented (for clustering incidents):**
- `endpoint_class` (not raw route with ids), `method`, `status_code`
- `channel` (web|app|partner), `customer_tier` (free|vip)
- `dependency_name` (which upstream failed), `error_class`
  (timeout|conn_refused|5xx|validation)

**Cardinality budget** - fewer than 10^-2 divergence per service:
- `service x env x region x endpoint_class x status_code` -> hundreds of
  series. Always fit in Grafana/Loki/Datadog (series cost).
- BANNED as tags: `user_id`, `request_id`, `trace_id`, `sku`, `order_id`,
  timestamps, query strings, raw customer emails. They belong to trace/log
  attributes (exemplar lookup picks ids when you need to correlate).
- Rule of thumb: if you would ever need to know "which product ids had the
  bug", that is a LOG query, not a timeseries dimension.

## 4. Clustering problems with decision tags

Incidents read top-down through tags:
1. SLO burn at edge -> break down by `status_code`, then `endpoint_class`
   (identifies: all endpoints or narrow?), then `channel` (all channels?)
2. If one `dependency_name` spikes -> that repo gate is the incident owner.
3. Cross-cut with `customer_tier` / `region` to size business impact before
   paging: "vip users lose / some vs. everyone lost".

In Datadog these are the `tag` filters on monitors and dashboards; same tag
set works in PromQL.

## 5. Business metrics for health

Business KPIs depend on the domain we serve, but shape is always the same:
- counter per meaningful transaction (created, succeeded, failed_by_reason)
  with tags that support clustering (`channel`, `region`, `error_class`);
- alert on burn of business KPI - flag pages when revenue-relevant traffic
  is broken (e.g. `orders_created_total:rate` falls to below 50% of trailing
  7d SAME-HOUR baseline).

## 6. Datadog crosswalk

| This repo | Datadog equivalent |
|---|---|
| Prom label | tag |
| Dashboard as code (provisioning) | dashboards as terraform (`datadog` provider) |
| Burn-rate alert (`slo-alerts.yml`) | monitors + SLO tracking (error budget burn) |
| Exemplar click to Tempo | DD marker to trace (APM integration) |
| Loki log line w/ trace_id | logs pipeline with trace_id attribute -> logs explorer |
| `docker compose` repro | terraform module + private network zone |

Tag discipline is the reason it costs less there: same taxonomy prevents
colossally high-cardinality custom metrics.

## 7. Checklist to add a metric

1. Which tier? (RED / USE / business)
2. Naming convention + unit suffix?
3. Which tags, minimal-but-decision-grade set?
4. Estimate cardinality - number a metric-of-metric bounds.
5. Which dashboard/monitor consumes it (as code)?
6. Alert? (must link to runbook; only tier 1 + business KPIs page)
