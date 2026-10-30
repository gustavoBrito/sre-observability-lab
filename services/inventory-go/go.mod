module github.com/your-user/sre-observability-lab/services/inventory-go

go 1.24

require (
	github.com/prometheus/client_golang v1.21.0
	go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp v0.60.0
	go.opentelemetry.io/otel v1.35.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.35.0
	go.opentelemetry.io/otel/sdk v1.35.0
)
