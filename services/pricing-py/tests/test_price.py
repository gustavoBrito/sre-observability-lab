"""Coverage of pricing behavior routed through the layered app:
router -> service -> repositories. Failure/tail paths forced via RNG seams."""

from fastapi.testclient import TestClient

from pricing import main
from pricing.models.price import Stock
from pricing.repositories import persistence
from pricing.repositories.inventory_repository import InventoryUnavailable
from pricing.routers import price as price_router
from pricing.services import pricing_service
from pricing.services.pricing_service import PricingService

client = TestClient(main.app)


class _StubInventory:
    def __init__(self, fail: bool = False):
        self.fail = fail

    async def get_stock(self, sku: str) -> Stock:
        if self.fail:
            raise InventoryUnavailable("inventory returned 503")
        return Stock(sku=sku, units=5)


def _install(inventory=_StubInventory()):
    price_router.svc = PricingService(inventory=inventory)


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_quote_happy_path(monkeypatch):
    monkeypatch.setattr(persistence, "rng01", lambda: 0.5)     # no persistence fail
    monkeypatch.setattr(pricing_service, "work_duration", lambda a, b: 0.01)
    monkeypatch.setattr(pricing_service, "tail01", lambda: 0.5)  # no heavy tail
    _install()

    resp = client.get("/price", params={"sku": "SKU-42"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["units"] == 5
    assert body["price_usd"] > 0


def test_persistence_error_maps_to_500(monkeypatch):
    monkeypatch.setattr(persistence, "rng01", lambda: 0.001)  # < 5% -> failure
    _install()

    resp = client.get("/price")

    assert resp.status_code == 500
    assert "persistence unavailable" in resp.text


def test_heavy_tail_latency_path(monkeypatch):
    monkeypatch.setattr(persistence, "rng01", lambda: 0.5)
    tail = iter([0.005])
    monkeypatch.setattr(pricing_service, "tail01", lambda: next(tail))
    monkeypatch.setattr(pricing_service, "work_duration", lambda a, b: 0.01)
    _install()

    resp = client.get("/price")

    assert resp.status_code == 200


def test_inventory_upstream_error_maps_to_502(monkeypatch):
    monkeypatch.setattr(persistence, "rng01", lambda: 0.5)
    _install(_StubInventory(fail=True))

    resp = client.get("/price")

    assert resp.status_code == 502
    assert "inventory error" in resp.text


def test_metrics_contract_registered():
    assert "endpoint" in main.REQUESTS._labelnames
    assert "status_code" in main.REQUESTS._labelnames
