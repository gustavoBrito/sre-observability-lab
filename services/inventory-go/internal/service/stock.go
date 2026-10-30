// Package service - business use cases. Depends on models + repository only:
// no HTTP, no Prometheus, no OTel SDK imports here.

package service

import (
	"errors"

	"inventory/internal/models"
	"inventory/internal/repository"
)

var (
	// ErrInvalidSku: malformed input -> 400 at the edge.
	ErrInvalidSku = errors.New("sku required")
	// ErrUnavailable: storage degraded -> 500 at the edge.
	ErrUnavailable = repository.ErrReadFailure
)

// Stock resolves current stock for a SKU; heavy tail ~1% injected.
func Stock(sku string) (models.Stock, error) {
	if sku == "" {
		return models.Stock{}, ErrInvalidSku
	}

	repository.SimulatedWork()

	units, err := repository.PersistedUnits()
	if err != nil {
		return models.Stock{}, ErrUnavailable
	}

	if repository.Rng01() < 0.01 { // injected heavy-tail branch
		repository.HeavyTail()
	}

	return models.Stock{SKU: sku, Units: units}, nil
}
