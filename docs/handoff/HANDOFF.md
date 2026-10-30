# Handoff — continuidade deste projeto

Última atualização: 2026-10-30 · Fase: **no ar, CI verde** — passe o bastão.

Este arquivo É O handoff de mercado para continuidade entre pessoas/sessões:
snapshot de estado, decisões, dívidas conhecidas e lista do próximo passo.
Regra: quem terminou um ciclo de trabalho **atualiza este arquivo no mesmo PR**.

## Estado em uma frase

Lab de observabilidade com BFF Node -> FastAPI/Go, OTel end-to-end, SLOs com
burn-rate, tudo reportado em docs as-code — e agents governados por AGENTS.md.

## Snapshot técnico

| Área | Estado |
|---|---|
| CI (5 jobs) | verde: validate, test-python, test-go, test-node, security |
| Cobertura | 95% python · 95,1% go (business) · 90/85% node thresholds |
| Security | 0 vuln (govulncheck + npm audit); pip-audit limpo |
| Repo | https://github.com/gustavoBrito/sre-observability-lab (main) |
| Repos local | `C:\gugad\dev\sre-observability-lab` (jamais em OneDrive) |

## Decisões registradas (onde buscar contexto)

1. `docs/adr/0001-otel-collector.md` — traces/logs via Collector; métricas de
   SLO com schema estável e scrape direto (contrato de nomes).
2. `docs/architecture.md` — dependência dirigida `bff -> pricing -> inventory`,
   edges thin, gateways com timeout, sem cross-calls.
3. `docs/testing-policy.md` — cobertura como gate; inj de RNG como seam.
4. `AGENTS.md` — Pré-requisitos para qualquer agente/humano; DoD em gates.

## Dívidas / vigia ativa

- [ ] `security` job: `npm audit --audit-level=high` é passar; re-verificar
      após qualquer bump do OTel JS (pin de versão = contrato).
- [ ] Adicionar badge do CI no README (1 linha).
- [ ] Compose ainda não foi executado numa máquina com Docker (validado em
      CI via `docker compose config -q`); primeira execução pode exigir
      ajustes de versão de imagens (otel-collector 0.122, tempo 2.7, loki 3.4).
- [ ] ROADMAP: Alertmanager, blackbox, Helm, client React no BFF.

## Próximos passos (ordem sugerida)

1. Subir o Docker Desktop e validar `docker compose up --build` ponta a ponta.
2. Badge + screenshots do Grafana nos posts de LinkedIn (ver CHANGELOG 0.2.0).
3. 4-week LinkedIn das técnicas derivadas do repo (ADR-0001, burn-rate...)
4. Refino de métricas de negócio seguindo `docs/metrics-strategy.md`.

## Como rodar em 30 segundos

```bash
docker compose up --build
# Grafana http://localhost:3000 (anon viewer) · README com mapa completo
```

## Owner

- Repo: gustavoBrito · GitHub: @gustavoBrito · dedo-duro de AGENTS.md
