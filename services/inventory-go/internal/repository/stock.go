// Package repository - persistence gateway (simulated data source).
// Failure/latency injection goes through the rng01 seam so tests force both
// paths deterministically (docs/testing-policy.md).

package repository

import (
	"errors"
	"math/rand"
	"time"
)

// rng01 is the injectable RNG seam; production default = real randomness.
var rng01 = func() float64 { return rand.Float64() }

// Rng01 draws from the seam (service layer uses it for cross-cutting rolls).
func Rng01() float64 { return rng01() }

// SetRng01 replaces the seam; tests call RestoreRng01 via defer.
func SetRng01(f func() float64) { rng01 = f }

// RestoreRng01 goes back to production randomness.
func RestoreRng01() { rng01 = func() float64 { return rand.Float64() } }

// RepositoryError is the sentinel type for storage failures.
var ErrReadFailure = errors.New("persistence read failure")

// PersistedUnits returns current units for a SKU; ~2% availability failure.
func PersistedUnits() (int, error) {
	if rng01() < 0.02 {
		return 0, ErrReadFailure
	}
	return rand.Intn(200), nil //nolint:gosec // simulated data
}

// SimulatedWork sleeps the base read latency (10-80ms).
func SimulatedWork() {
	time.Sleep(time.Duration(10+rand.Intn(70)) * time.Millisecond) //nolint:gosec // simulated work
}

// HeavyTail sleeps the heavy-tail branch (300-900ms).
func HeavyTail() {
	time.Sleep(time.Duration(300+rand.Intn(600)) * time.Millisecond)
}
