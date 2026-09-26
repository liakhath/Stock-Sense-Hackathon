import pytest
from fastapi.testclient import TestClient

from app.engine import StockEngine
from app.main import create_app

STAFF = {"X-User": "staff"}
MANAGER = {"X-User": "manager"}


@pytest.fixture
def client():
    return TestClient(create_app(StockEngine(adjustment_approval_threshold=10)))


@pytest.fixture
def setup(client):
    loc = client.post("/api/locations", json={"name": "Main", "warehouse": "WH1"}).json()
    p = client.post("/api/products",
                    json={"name": "Steel", "sku": "STL-1", "uom": "kg", "min_qty": 20}).json()
    r = client.post("/api/operations/receipts",
                    json={"location_id": loc["id"], "lines": [{"product_id": p["id"], "qty": 100}]},
                    headers=STAFF).json()
    client.post(f"/api/operations/{r['id']}/validate", headers=STAFF)
    return loc, p, r


def test_full_flow(client, setup):
    loc, p, r = setup
    assert r["lines"][0]["sku"] == "STL-1"
    assert client.get(f"/api/operations/{r['id']}").json()["validated_by"] == "staff"

    d = client.post("/api/operations/deliveries",
                    json={"location_id": loc["id"], "lines": [{"product_id": p["id"], "qty": 500}]}).json()
    res = client.post(f"/api/operations/{d['id']}/validate")
    assert res.status_code == 409 and res.json()["code"] == "InsufficientStock"

    assert client.get(f"/api/products/{p['id']}/stock").json()["on_hand"] == 100
    assert client.get("/api/dashboard/kpis").json()["pending_deliveries"] == 1
    assert len(client.get("/api/ledger").json()) == 1
    assert client.get("/api/products", params={"q": "stl"}).json()[0]["stock_status"] == "in_stock"
    assert client.get("/api/products/sku/stl-1").json()["id"] == p["id"]
    waiting = client.get("/api/operations", params={"type": "delivery", "status": "waiting"}).json()
    assert [o["id"] for o in waiting] == [d["id"]]


def test_approval_flow(client, setup):
    loc, p, _ = setup
    a = client.post("/api/operations/adjustments",
                    json={"location_id": loc["id"], "reason": "lost",
                          "lines": [{"product_id": p["id"], "qty": 50}]},
                    headers=STAFF).json()
    assert client.post(f"/api/operations/{a['id']}/validate", headers=STAFF).status_code == 403
    assert client.post(f"/api/operations/{a['id']}/approve", headers=STAFF).status_code == 400
    assert client.post(f"/api/operations/{a['id']}/approve", headers=MANAGER).status_code == 200
    assert client.post(f"/api/operations/{a['id']}/validate", headers=STAFF).json()["status"] == "done"


def test_update_and_reverse(client, setup):
    _, p, r = setup
    upd = client.patch(f"/api/products/{p['id']}", json={"min_qty": 30}).json()
    assert upd["min_qty"] == 30
    rev = client.post(f"/api/operations/{r['id']}/reverse", headers=MANAGER)
    assert rev.status_code == 201 and rev.json()["reverses_id"] == r["id"]
    assert client.get(f"/api/products/{p['id']}/stock").json()["on_hand"] == 0


def test_errors(client):
    assert client.get("/api/products/999").status_code == 404
    assert client.post("/api/products", json={"name": "", "sku": "x"}).status_code == 422
    assert client.get("/api/operations", params={"type": "bogus"}).status_code == 422


def test_seeded_app_runs():
    from app.main import app
    c = TestClient(app)
    assert c.get("/api/health").json() == {"status": "ok"}
    assert c.get("/api/dashboard/kpis").json()["total_products_in_stock"] > 0