// Bootstrap only (wiring): OTel exporter/provider, HTTP servers, env.
// Business lives in internal/service, HTTP edges in internal/handlers.

package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"

	"inventory/internal/handlers"
)

func envOr(k, fallback string) string {
	if v := os.Getenv(k); v != "" {
		return strings.TrimSpace(v)
	}
	return fallback
}

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	exporter, err := otlptracegrpc.New(ctx)
	if err != nil {
		slog.Error("failed to create OTLP exporter", "error", err)
		os.Exit(1)
	}

	res, err := resource.New(ctx, resource.WithFromEnv(), resource.WithProcess())
	if err != nil {
		slog.Error("failed to create resource", "error", err)
		os.Exit(1)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)
	defer func() {
		if err := tp.Shutdown(ctx); err != nil && !errors.Is(err, context.Canceled) {
			slog.Error("trace provider shutdown error", "error", err)
		}
	}()
	otel.SetTracerProvider(tp)

	addr := ":" + envOr("PORT_HTTP", "8003")
	mux := http.NewServeMux()
	mux.Handle("/stock", otelhttp.NewHandler(http.HandlerFunc(handlers.Stock), "stock"))
	mux.Handle("/healthz", otelhttp.NewHandler(http.HandlerFunc(handlers.Health), "healthz"))

	port := envOr("PORT_METRICS", "9003")
	go func() {
		if err := http.ListenAndServe(":"+port, promhttp.Handler()); err != nil {
			slog.Error("metrics server failed", "error", err)
		}
	}()

	srv := &http.Server{Addr: addr, Handler: mux}
	slog.Info("inventory listening", "http", addr, "metrics", port)

	if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		slog.Error("http server failed", "error", err)
		os.Exit(1)
	}

	<-ctx.Done()
}
