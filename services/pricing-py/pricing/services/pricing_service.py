"""Use case: pricing quote. Business rules + failure/tail-latency simulation.

Depends only on models + repositories. No HTTP, no Prometheus, no FastAPI
imports here - those belong to the edges.
"""

import asyncio
import logging
import random

from pricing.repositories import persistence
from pricing.repositories.inventory_repository import (
    InventoryRepository,
    InventoryUnavailable,
)

log = logging.getLogger(__name__)


# Injectable seams: default = real randomness; tests override these.
work_duration = random.uniform
tail01 = random.random


class PricingService:
    def __init__(self, inventory: InventoryRepository | None = None):
        self._inventory = inventory or InventoryRepository()

    async def quote(self, sku: str) -> dict:
        await asyncio.sleep(work_duration(0.02, 0.12))  # simulated work

        base = await persistence.read_base_price(sku)  # 5% injected failure

        if tail01() < 0.01:
            await asyncio.sleep(random.uniform(0.8, 1.5))
            log.warning("heavy-tail latency hit on sku=%s", sku)

        stock = await self._inventory.get_stock(sku)  # 502 on upstream failure

        log.info("quote computed sku=%s units=%s", sku, stock.units)
        return {"sku": sku, "price_usd": base, "units": stock.units}


# Module-level singleton, thin routers reach it (and tests replace it).
service = PricingService()
