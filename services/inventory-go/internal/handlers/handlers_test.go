package handlers_test

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"inventory/internal/handlers"
	"inventory/internal/repository"
)

func setRng(returns []float64) func() {
	repository.SetRng01(func() float64 {
		if len(returns) == 0 {
			return 0.5
		}
		v := returns[0]
		returns = returns[1:]
		return v
	})
	return repository.RestoreRng01
}

func TestHealth(t *testing.T) {
	r := httptest.NewRequest("GET", "/healthz", nil)
	w := httptest.NewRecorder()
	handlers.Health(w, r)
	if w.Code != 200 || !strings.Contains(w.Body.String(), `"status":"ok"`) {
		t.Fatalf("want 200 ok, got %d %s", w.Code, w.Body.String())
	}
}

func TestStock(t *testing.T) {
	t.Run("happy path returns stock", func(t *testing.T) {
		defer setRng([]float64{0.8})() // no failure, no tail
		r := httptest.NewRequest("GET", "/stock?sku=SKU-42", nil)
		w := httptest.NewRecorder()
		handlers.Stock(w, r)
		if w.Code != 200 || !strings.Contains(w.Body.String(), `"units"`) {
			t.Fatalf("want 200 with units, got %d %s", w.Code, w.Body.String())
		}
	})

	t.Run("missing sku is bad request", func(t *testing.T) {
		defer setRng([]float64{})()
		r := httptest.NewRequest("GET", "/stock?sku=", nil)
		w := httptest.NewRecorder()
		handlers.Stock(w, r)
		if w.Code != 400 {
			t.Fatalf("want 400, got %d", w.Code)
		}
	})

	t.Run("injected failure surfaces 500", func(t *testing.T) {
		defer setRng([]float64{0.001})() // < 0.02 -> read failure
		r := httptest.NewRequest("GET", "/stock?sku=SKU-42", nil)
		w := httptest.NewRecorder()
		handlers.Stock(w, r)
		if w.Code != 500 {
			t.Fatalf("want 500, got %d", w.Code)
		}
	})

	t.Run("injected heavy tail delays response", func(t *testing.T) {
		defer setRng([]float64{0.8, 0.001})() // no failure; tail fires
		r := httptest.NewRequest("GET", "/stock?sku=SKU-42", nil)
		start := time.Now()
		w := httptest.NewRecorder()
		handlers.Stock(w, r)
		if w.Code != 200 {
			t.Fatalf("want 200, got %d", w.Code)
		}
		if time.Since(start) < 290*time.Millisecond {
			t.Fatalf("tail latency not applied")
		}
	})
}
