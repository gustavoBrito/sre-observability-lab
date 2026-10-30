// Package handlers - interface adapters (thin): parse -> service -> write.
// All status codes and RED recording come from here; business decisions in
// service only.

package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"inventory/internal/models"
	"inventory/internal/observability"
	"inventory/internal/service"
)

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	observability.Status(w, code)
	_ = json.NewEncoder(w).Encode(v)
}

// Stock: GET /stock?sku=...
func Stock(w http.ResponseWriter, r *http.Request) {
	start := observability.Started()
	defer func() {
		observability.ReqLatency.WithLabelValues("GET").
			Observe(time.Since(start).Seconds())
	}()

	stock, err := service.Stock(r.URL.Query().Get("sku"))
	switch {
	case err == nil:
		writeJSON(w, http.StatusOK, stock)
	case errors.Is(err, service.ErrInvalidSku):
		writeJSON(w, http.StatusBadRequest, models.Stock{})
	default:
		writeJSON(w, http.StatusInternalServerError, models.Stock{})
	}
}

// Health: GET /healthz (also feeds the "status" metric - consistent RED).
func Health(w http.ResponseWriter, _ *http.Request) {
	start := observability.Started()
	defer func() {
		observability.ReqLatency.WithLabelValues("GET").
			Observe(time.Since(start).Seconds())
	}()
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}
