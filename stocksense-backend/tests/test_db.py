"""Persistence tests. Use a throwaway SQLite file by default.
To also test against Postgres, set TEST_DATABASE_URL to a DISPOSABLE database (never Supabase prod)."""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.seed import seed_demo
from app.db import tables as t
from app.db.repository import PersistentStore
from app.engine import StockEngine
from app.main import create_app

pytestmark = pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")  # SQLite + Decimal

PG_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(params=["sqlite"] + (["postgres"] if PG_URL else []))
def db_url(request, tmp_path):
    if request.param == "sqlite":
        return f"sqlite:///{tmp_path / 'test.db'}"
    PersistentStore(PG_URL).drop_schema()            # clean slate
    return PG_URL


def boot(url):
    """Simulate a server start: load everything from the DB."""
    store = PersistentStore(url).load()
    return StockEngine(store=store, adjustment_approval_threshold=10), store


def test_data_survives_restart(db_url):
    eng, store = boot(db_url)
    seed_demo(eng)
    store.save()
    kpis = eng.dashboard_kpis()
    ops = {o.ref: (o.status, o.created_by) for o in eng.list_operations()}
    history = [(e.operation_ref, e.qty, e.user) for e in eng.move_history()]

    eng2, _ = boot(db_url)                            # "restart"
    assert eng2.dashboard_kpis() == kpis
    assert {o.ref: (o.status, o.created_by) for o in eng2.list_operations()} == ops
    assert [(e.operation_ref, e.qty, e.user) for e in eng2.move_history()] == history
    assert eng2.get_product_by_sku("STL-001").min_qty == 50


def test_ids_and_refs_continue_after_restart(db_url):
    eng, store = boot(db_url)
    seed_demo(eng)                                    # 4 locations, receipts WH/IN/0001-0002
    store.save()

    eng2, store2 = boot(db_url)
    loc = eng2.add_location("Dock", "Warehouse 3")
    assert loc.id == 5
    r = eng2.create_receipt(loc.id, [(eng2.get_product_by_sku("CHR-001").id, 5)], user="manager")
    assert r.ref == "WH/IN/0003"
    eng2.validate(r.id, user="manager")
    store2.save()

    eng3, _ = boot(db_url)
    assert eng3.quant_at(eng3.get_product_by_sku("CHR-001").id, loc.id).on_hand == 5
    assert eng3.move_history()[0].operation_ref == "WH/IN/0003"


def test_only_changes_are_written(db_url):
    eng, store = boot(db_url)
    seed_demo(eng)
    assert store.save() > 0
    assert store.save() == 0                          # nothing changed -> no writes
    eng.update_product(eng.get_product_by_sku("STL-001").id, min_qty=75)
    assert store.save() == 1                          # just that one product row

    eng2, _ = boot(db_url)
    assert eng2.get_product_by_sku("STL-001").min_qty == 75


def test_waiting_and_reservations_persist(db_url):
    eng, store = boot(db_url)
    loc = eng.add_location("Stock", "WH1")
    p = eng.add_product("Steel", "STL-1", initial_stock=10, location_id=loc.id)
    d = eng.confirm(eng.create_delivery(loc.id, [(p.id, 4)]).id)     # reserves 4
    store.save()

    eng2, _ = boot(db_url)
    assert eng2.quant_at(p.id, loc.id).reserved == 4
    assert eng2.store.operations[d.id].status.value == "ready"
    eng2.validate(d.id)
    assert eng2.quant_at(p.id, loc.id).on_hand == 6


def test_api_writes_are_saved_automatically(db_url):
    eng, store = boot(db_url)
    client = TestClient(create_app(eng))
    loc = client.post("/api/locations", json={"name": "Main", "warehouse": "WH1"}).json()
    p = client.post("/api/products", json={"name": "Steel", "sku": "STL-1", "uom": "kg"}).json()
    r = client.post("/api/operations/receipts", headers={"X-User": "staff"},
                    json={"location_id": loc["id"], "lines": [{"product_id": p["id"], "qty": 30}]}).json()
    client.post(f"/api/operations/{r['id']}/validate", headers={"X-User": "staff"})
    assert client.get("/api/health").json()["storage"] == "database"

    eng2, store2 = boot(db_url)                       # no manual save() - middleware did it
    assert eng2.total_on_hand(p["id"]) == 30
    assert eng2.move_history()[0].user == "staff"
    with store2.db.connect() as c:
        assert c.execute(select(func.count()).select_from(t.stock_ledger)).scalar() == 1
