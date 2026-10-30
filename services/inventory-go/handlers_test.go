package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// injectRnd saves/restores the injection seam so tests never bleed into each
// other (single-threaded package tests; guard with mutex if parallelized).
func injectRnd(returns []float64) func() {
	orig := nextRandom
	idx := 0
	nextRandom = func() float64 {
		if idx >= len(returns) {
			return 0.5
		}
		v := returns[idx]
		idx++
		return v
	}
	return func() { nextRandom = orig }
}

func doStock(t *testing.T, sku string) *httptest.ResponseRecorder {
	t.Helper()
	r := httptest.NewRequest(http.MethodGet, "/stock?sku="+sku, nil)
	w := httptest.NewRecorder()
	stockHandler(w, r)
	return w
}

func TestStockHandler(t *testing.T) {
	t.Run("happy path returns stock", func(t *testing.T) {
		restore := injectRnd([]float64{0.9}) // no error, no tail
		defer restore()

		w := doStock(t, "SKU-42")

		if w.Code != http.StatusOK {
			t.Fatalf("want 200, got %d", w.Code)
		}
		if !strings.Contains(w.Body.String(), `"units"`) {
			t.Fatalf("want units in body, got %q", w.Body.String())
		}
	})

	t.Run("missing sku is bad request", func(t *testing.T) {
		w := doStock(t, "")
		if w.Code != http.StatusBadRequest {
			t.Fatalf("want 400, got %d", w.Code)
		}
	})

	t.Run("injected error surfaces 500", func(t *testing.T) {
		restore := injectRnd([]float64{0.001})
		defer restore()

		w := doStock(t, "SKU-42")

		if w.Code != http.StatusInternalServerError {
			t.Fatalf("want 500, got %d", w.Code)
		}
	})

	t.Run("injected heavy tail latency delays response", func(t *testing.T) {
		restore := injectRnd([]float64{0.9, 0.001}) // no error; tail fires
		defer restore()

		start := time.Now()
		w := doStock(t, "SKU-42")

		if w.Code != http.StatusOK {
			t.Fatalf("want 200, got %d", w.Code)
		}
		if elapsed := time.Since(start); elapsed < 290*time.Millisecond {
			t.Fatalf("tail latency not injected, elapsed=%s", fmt.Sprint(elapsed))
		}
	})
}
