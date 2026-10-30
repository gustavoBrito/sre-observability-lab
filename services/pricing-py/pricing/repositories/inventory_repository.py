"""Gateway to the inventory service.

All outbound HTTP lives here - so trace propagation (httpx instrumentation),
timeouts and error translation have exactly one place to change.
"""

import httpx

from pricing.models.price import Stock


class InventoryUnavailable(Exception):
    """Upstream failed - maps to 5xx at the edge."""


class InventoryRepository:
    def __init__(self, base_url: str | None = None, timeout: float = 3.0):
        self._base_url = base_url or INVENTORY_URL
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get_stock(self, sku: str) -> Stock:
        resp = await self._client.get(f"{self._base_url}/stock", params={"sku": sku})
        if resp.status_code != 200:
            raise InventoryUnavailable(f"inventory returned {resp.status_code}")
        return Stock(**resp.json())


# Deployment config drives the address (12-factor style)
INVENTORY_URL = __import__("os").environ.get("INVENTORY_URL", "http://inventory:8003")
