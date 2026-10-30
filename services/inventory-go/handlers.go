// Business logic of the inventory service. Kept separate from main.go so the
// coverage gate (docs/testing-policy.md) measures exactly this file and never
// dilutes "achievable" numbers with untestable bootstrap wiring.

package main

import (
	"fmt"
	"log/slog"
	"math/rand"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
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
