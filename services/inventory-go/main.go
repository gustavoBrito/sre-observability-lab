// Inventory service (Go) - deepest hop of the distributed trace.
// Chain: bff -> pricing -> inventory
// Demonstrates: manual OTel setup, otelhttp server instrumentation for trace
// context propagation, and Prometheus exposition via client_golang.
//
// Failure injection goes through an injectable RNG seam (nextRandom) so unit
// tests force both the error and heavy-tail paths deterministically.

package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
)

// First-class metrics - names are a contract with prometheus/rules/slo-alerts.yml
var (
	reqTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "inventory_http_requests_total",
			Help: "HTTP requests handled by inventory",
		},
		[]string{"method", "status_code"},
	)
	reqLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "inventory_http_request_duration_seconds",
			Help: "Inventory request latency in seconds",
			Buckets: []float64{0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5},
		},
		[]string{"method"},
	)
)

func init() {
	prometheus.MustRegister(reqTotal, reqLatency)
}

func status(w http.ResponseWriter, code int) {
	reqTotal.WithLabelValues("GET", strconv.Itoa(code)).Inc()
	w.WriteHeader(code)
}

// stockHandler: ~2% hard errors, ~1% heavy-tail latency (300-900ms).
func stockHandler(w http.ResponseWriter, r *http.Request) {
	t0 := time.Now()
	defer func() {
		reqLatency.WithLabelValues("GET").Observe(time.Since(t0).Seconds())
	}()

	sku := strings.TrimSpace(r.URL.Query().Get("sku"))
	if sku == "" {
		status(w, http.StatusBadRequest)
		return
	}

	time.Sleep(time.Duration(10+rand.Intn(70)) * time.Millisecond) //nolint:gosec // simulated work

	if nextRandom() < 0.02 { // injected failure
		slog.Error("stock read failed", "sku", sku)
		status(w, http.StatusInternalServerError)
		return
	}

	if nextRandom() < 0.01 { // injected tail latency
		time.Sleep(time.Duration(300+rand.Intn(600)) * time.Millisecond)
	}

	w.Header().Set("Content-Type", "application/json")
	status(w, http.StatusOK)
	_, _ = fmt.Fprintf(w, `{"sku":%q,"units":%d}`, sku, rand.Intn(200)) //nolint:gosec // simulated data
}

func healthHandler(w http.ResponseWriter, _ *http.Request) {
	status(w, http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"ok"}`))
}

// nextRandom is the injectable seam for failure/tail-latency injection.
// Defaults to rand.Float64(); tests override it for deterministic paths.
var nextRandom = func() float64 { return rand.Float64() }

func main() {
	// Traces: OTLP grpc to the collector endpoint from env (deployment config)
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
	mux.Handle("/stock", otelhttp.NewHandler(http.HandlerFunc(stockHandler), "stock"))
	mux.Handle("/healthz", otelhttp.NewHandler(http.HandlerFunc(healthHandler), "healthz"))

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

func envOr(k, fallback string) string {
	if v := os.Getenv(k); v != "" {
		return strings.TrimSpace(v)
	}
	return fallback
}
