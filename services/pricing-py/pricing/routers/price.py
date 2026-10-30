"""HTTP edge (interface adapters): parse, delegate, map failures to codes.

Business decisions do NOT live here - routes stay skinny (two excepts).
"""

import logging

from fastapi import APIRouter, HTTPException

from pricing.models.price import PriceQuote
from pricing.repositories import persistence
from pricing.repositories.inventory_repository import InventoryUnavailable
from pricing.services import pricing_service
from pricing.services.pricing_service import PricingService

log = logging.getLogger(__name__)

router = APIRouter()

# Test seam: module-level service instance (tests replace it via monkeypatch)
svc: PricingService = pricing_service.service


@router.get("/price", response_model=PriceQuote)
async def price(sku: str = "SKU-42"):
    try:
        return await svc.quote(sku)
    except persistence.PersistenceUnavailable:
        log.error("persisting failed for sku=%s", sku)
        raise HTTPException(status_code=500, detail="persistence unavailable")
    except InventoryUnavailable:
        raise HTTPException(status_code=502, detail="inventory error")


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}
