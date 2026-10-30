// Package observability holds the CONTRACT metrics (cross-cutting telemetry).
// Names here are a contract with prometheus/rules/slo-alerts.yml. Leaf only.

package observability

import (
	"net/http"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

var (
	ReqTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "inventory_http_requests_total",
			Help: "HTTP requests handled by inventory",
		},
		[]string{"method", "status_code"},
	)
	ReqLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "inventory_http_request_duration_seconds",
			Help: "Inventory request latency in seconds",
			Buckets: []float64{0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5},
		},
		[]string{"method"},
	)
)

func init() {
	prometheus.MustRegister(ReqTotal, ReqLatency)
}

// Status writes the response AND records its outcome (RED).
func Status(w http.ResponseWriter, code int) {
	ReqTotal.WithLabelValues("GET", strconv.Itoa(code)).Inc()
	w.WriteHeader(code)
}

// Started returns a start time (symmetry helper for deferred latency records).
func Started() time.Time { return time.Now() }
