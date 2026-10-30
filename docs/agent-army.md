# Agent army - the roster

The exército de agentes that operates this repo, based on ADR-0004. Each one
lives as an OpenCode V2 agent file in `.opencode/agents/`; the `commander` is
the ONLY primary agent - everyone else runs as subagent with scoped
permissions. Human confirms push; CI is the only source of "green".

## Roster (v1: 10 agents)

| Agent | Role | Writes | Read-only parts |
|---|---|---|---|
| `commander` | Orchestrator: decomposes prompt, launches agents, integrates, enforces DoD | - (assembles it all) | everything |
| `architect` | Layers, dependency direction, ADRs, structural compliance | `docs/**` only | code review |
| `security` | Supply chain, leakage, attack surface; audits | nothing (report only) | everything |
| `integrator` | Implements features/integrations in the layered structure | code + tests (not `docs/adr/**`) | runs language suites |
| `reviewer` | Judges diff vs AGENTS.md DoD; APPROVED/CHANGES_REQUESTED | nothing | everything |
| `telemetry` | Metrics tiers, contract names, low-card tags, logs, alerts, runbooks | `prometheus/**`, `grafana/**`, `**/observability/**`, metric/runbook/slo docs | dashboards |
| `rollout` | Release plan: order per service, canary, success criteria, rollback, comms | `docs/rollouts/**`, `CHANGELOG.md`, `docs/handoff/HANDOFF.md` | everything else |
| `chaos` | Proves failure paths: seams, alerts fire, dashboards react | `services/**/tests/**` | runs scenarios |
| `triage` | Incident response: alert -> runbook -> query -> diagnosis | nothing | dashboards, logs, traces, history |
| `curator` | Turns proven milestones into public narrative (README hub, portfolio/posts) | `README.md`, `docs/**`, `portfolio/**` | everything |

## Example decomposition

Prompt: *"Adicione no pricing uma integração via API do Jira para trazer as
tarefas mais recentes."*

1. `architect` — onde esta integração entra? (novos ADRs? chamada outbound
   nova: `repositories/jira_repository.py`, config por env, contrato de
   endpoint);
2. `integrator` — implementa `JiraRepository` (httpx instrumentado, timeout,
   seams para teste) + testes >= 90%;
3. `telemetry` — `pricing_jira_tasks_fetched_total{outcome}` (tier business/
   USE), tags de decisão (`outcome=ok|auth|rate_limit|timeout`), dashboard,
   sem tag de alta cardinalidade;
4. `security` — token via env, nunca commitado; audita diffs;
5. `reviewer` — executa o checklist da DoD sobre o diff completo;
6. `chaos` — simula timeout/quota do Jira e prova o degradação + métrica;
7. `rollout` — plano: rollout por serviço, flag de feature (env), critério
   de sucesso vs baseline, rollback;
8. `commander` — integra tudo, roda os gates locais, mostra o resumo (diff +
   status de cada gate) e ESPERA o dono confirmar o push.

## Adding a new agent

1. `.opencode/agents/<name>.md` (frontmatter: `mode: subagent`, scoped
   `permissions`, `color`);
2. Add one line to the commander allowlist;
3. Add one row here.

## Future roles (propostos, não implementados)

- `performance`: análise de latência e saturação a partir dos histogramas;
- `cost` (FinOps): custo por série de métricas/volume de ingestão;
- `release-ops`: mecânica de PRs, badges, espera de CI (via gh CLI) - hoje o
  commander faz com confirmação humana.
