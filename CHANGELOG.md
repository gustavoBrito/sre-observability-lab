# Changelog

Formato de mercado: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.3.0/) +
[SemVer](https://semver.org/lang/pt-BR/). Toda mudança relevante entra aqui;
nada entra no histórico sem estar descrita.

## [0.2.0] — 2026-10-30

### Added
- Estrutura em camadas nos 3 serviços: `handlers/routes -> service ->
  models + repositories`, `observability/` como leaf (`cmd/` + `internal/` no Go,
  `pricing/` no Python, `src/` no Node).
- Governance como código: `docs/architecture.md` (contrato de dependência),
  `docs/testing-policy.md` (gate >= 90%), `docs/adr/0000-template.md`,
  `docs/adr/0001-otel-collector.md`, `AGENTS.md` com Definition of Done em gates.
- Gates de CI por linguagem: coverage >= 90% ponderado (Go com dedupe de
  `-coverpkg`), jest/supertest, pytest + stub de inventory em conftest.
- Supply chain: pip-audit, govulncheck (OTel SDK atualizado por GO-2026-4394),
  npm audit com lockfile (`npm ci` no CI e Dockerfile).
- `docs/slo.md`, runbooks de burn-rate, dashboard RED+SLO provisionado.
- `docs/handoff/HANDOFF.md`, `docs/components.md`, `docs/metrics-strategy.md`.

### Changed
- OTel JS: `sdk-node@0.300`, `api@1.10`, `auto-instrumentations@0.82` +
  `express` atualizado por advisory (0 vuln no npm audit).
- Go `toolchain 1.27` + `otel v1.47` / `x/net@latest` (govulncheck: 0 vulns
  em código).

### Security
- Lockfile do BFF commitado como contrato de supply chain; audit gates rodam
  em todo push; o job `security` é não-bloqueante com triage em issues.

## [0.1.0] — 2026-10-30

### Added
- Repositório inicial: BFF Node `:8000` -> pricing FastAPI `:8002` ->
  inventory Go `:8003`, OTel Collector -> Tempo/Loki, Prometheus com
  burn-rate de SLO, Grafana provisionado, loadgen, CI (yamllint/ruff/compose).
