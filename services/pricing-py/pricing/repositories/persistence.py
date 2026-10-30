"""Persistence gateway: reads the base price (a "database" in the lab).

Failure injection goes through an injectable RNG seam (rng01) so tests force
the degradation path deterministically. In real env, replace this module
with the actual DB adapter without touching services.
"""

import asyncio
import logging
import random

log = logging.getLogger(__name__)


class PersistenceUnavailable(Exception):
    """Storage layer failed - maps to 500 at the edge."""


# Injectable seam: default = real randomness; tests override it.
rng01 = random.random

_STALE = {"price_usd": {}}  # in-mem stand-in for a real store


async def read_base_price(sku: str) -> float:
    await asyncio.sleep(0.02)
    if rng01() < 0.05:
        log.error("persistence read failed for sku=%s", sku)
        raise PersistenceUnavailable("persistence unavailable")
    stored = _STALE["price_usd"].get(sku)
    if stored is None:
        stored = random.uniform(10, 500)  #nolint:gosec,pylint # simulated data
        _STALE["price_usd"][sku] = stored
    return stored
