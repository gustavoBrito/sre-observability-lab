# Security Policy

## Reporting

This is a personal lab project — no production data is involved. Still, if you spot an issue (exposed credentials, misconfigured TLS, vulnerable dependency), open a GitHub issue with the `security` label or reach out via my GitHub profile email.

## Notes

- Container configs assume a local/lab network. Do not expose Tempo/Loki/Prometheus ports publicly without authentication (Grafana has anonymous view-only access on purpose, for demos).
- No secrets are committed; any credentials come from environment variables only.
