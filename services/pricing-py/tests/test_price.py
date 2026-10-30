"""Coverage of pricing behavior: happy path, injected errors, upstream error
mapping and tail-latency branch - all deterministic via RNG seams."""

from fastapi.testclient import TestClient

import main


class _StubResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _StubClient:
    def __init__(self, status_code: int):
        self.status_code = status_code

    async def get(self, url, params=None):  # match httpx.AsyncClient signature
        return _StubResponse(self.status_code)


client = TestClient(main.app)


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_price_happy_path(monkeypatch):
    monkeypatch.setattr(main.random, "random", lambda: 0.5)
    monkeypatch.setattr(main.random, "uniform", lambda a, b: 0.01)

    resp = client.get("/price", params={"sku": "SKU-42"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["units"] == 5
    assert "price_usd" in body


def test_persistence_error_maps_to_500(monkeypatch):
    monkeypatch.setattr(main.random, "random", lambda: 0.001)  # < 0.05 -> error

    resp = client.get("/price")

    assert resp.status_code == 500
    assert "persistence unavailable" in resp.text


def test_heavy_tail_latency_path(monkeypatch):
    calls = iter([0.5, 0.005])  # 1st: happy error roll; 2nd: tail branch
    monkeypatch.setattr(main.random, "random", lambda: next(calls))
    monkeypatch.setattr(main.random, "uniform", lambda a, b: 1.1)

    resp = client.get("/price")

    assert resp.status_code == 200


def test_inventory_upstream_error_maps_to_502(monkeypatch):
    monkeypatch.setattr(main.random, "random", lambda: 0.5)
    monkeypatch.setattr(main, "_http", _StubClient(503))

    resp = client.get("/price")

    assert resp.status_code == 502
    assert "inventory error" in resp.text


def test_metrics_recorded_after_requests():
    # happy-path test above already bumped it at least once
    assert "endpoint" in main.REQUESTS._labelnames
    assert "status_code" in main.REQUESTS._labelnames
    assert len(main.REQUESTS._metrics) >= 1
