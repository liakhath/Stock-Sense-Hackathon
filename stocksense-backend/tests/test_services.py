import io
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.engine import ApprovalRequired, StockEngine
from app.main import create_app
from app.services.alerts import AlertCenter
from app.services.analytics import movers, stock_csv, valuation
from app.services.importer import import_products

CSV = (
    "Product Name,SKU,Category,Unit,Min Stock,Reorder Qty,Cost,Qty,Warehouse,Location\n"
    "Steel Rod,STL-001,Raw,kg,50,200,65,100,Main Warehouse,Stock\n"
    "Chair,CHR-001,Furniture,unit,10,40,2500,,,\n"
    "Bad Row,,Misc,unit,1,1,1,,,\n"
    "Desk,DSK-001,Furniture,unit,abc,1,1,,,\n"
    "Chair Again,chr-001,Furniture,unit,1,1,1,,,\n"
).encode()


# ---------------- import ----------------
def test_import_dry_run_then_commit():
    eng = StockEngine()
    report = import_products(eng, "items.csv", CSV, dry_run=True)
    assert report["created"] == 2
    assert {e["row"] for e in report["errors"]} == {4, 5, 6}
    assert eng.store.products == {}                          # dry run saved nothing

    report = import_products(eng, "items.csv", CSV, dry_run=False, user="manager")
    assert report["created"] == 2
    steel = eng.get_product_by_sku("STL-001")
    assert steel.min_qty == 50 and eng.total_on_hand(steel.id) == 100
    assert eng.list_operations()[0].created_by == "manager"


def test_import_excel_updates_existing():
    eng = StockEngine()
    eng.add_product("Chair", "CHR-001", min_qty=5)
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "sku", "min_qty", "qty"])
    ws.append(["Office Chair", "chr-001", 12, 7])
    ws.append(["Lamp", "LMP-1", 3, None])
    buf = io.BytesIO()
    wb.save(buf)

    r = import_products(eng, "items.xlsx", buf.getvalue(), dry_run=False)
    assert r["updated"] == 1 and r["created"] == 1 and len(r["warnings"]) == 1
    chair = eng.get_product_by_sku("CHR-001")
    assert chair.name == "Office Chair" and chair.min_qty == 12


def test_import_rejects_bad_files():
    with pytest.raises(ValueError):
        import_products(StockEngine(), "x.pdf", b"123")
    with pytest.raises(ValueError):
        import_products(StockEngine(), "x.csv", b"foo,bar\n1,2\n")


# ---------------- analytics ----------------
def test_movers_and_valuation():
    eng = StockEngine()
    loc = eng.add_location("Stock", "WH1")
    a = eng.add_product("Fast", "F-1", category="A", unit_cost=10, initial_stock=100, location_id=loc.id)
    b = eng.add_product("Slow", "S-1", category="A", unit_cost=5, initial_stock=50, location_id=loc.id)
    eng.add_product("Dead", "D-1", category="B", unit_cost=2, initial_stock=10, location_id=loc.id)
    eng.validate(eng.create_delivery(loc.id, [(a.id, 60)]).id)
    eng.validate(eng.create_delivery(loc.id, [(b.id, 5)]).id)

    m = movers(eng, days=30, top=5)
    assert [r["sku"] for r in m["fast_movers"]] == ["F-1", "S-1"]
    assert m["fast_movers"][0]["shipped"] == 60
    assert [r["sku"] for r in m["slow_movers"]] == ["S-1", "F-1"]
    assert [r["sku"] for r in m["dead_stock"]] == ["D-1"]

    v = valuation(eng)
    assert v["total"] == 645                                 # 40*10 + 45*5 + 10*2
    assert v["by_category"][0] == {"name": "A", "value": Decimal("625")}
    assert "F-1" in stock_csv(eng)


# ---------------- alerts ----------------
def test_alerts_create_and_resolve():
    eng = StockEngine(adjustment_approval_threshold=5)
    loc = eng.add_location("Stock", "WH1")
    p = eng.add_product("Steel", "STL-1", min_qty=10, initial_stock=8, location_id=loc.id)
    center = AlertCenter()

    assert [a.kind for a in center.refresh(eng)] == ["low_stock"]
    assert center.refresh(eng) == []                         # no duplicates

    eng.validate(eng.create_receipt(loc.id, [(p.id, 50)]).id)
    center.refresh(eng)
    assert center.list_alerts() == []                        # auto-resolved

    adj = eng.create_adjustment(loc.id, [(p.id, 0)], reason="lost", user="staff")
    with pytest.raises(ApprovalRequired):
        eng.validate(adj.id, user="staff")
    assert {a.kind for a in center.refresh(eng)} == {"approval_needed"}


def test_approval_alert_resolves_after_approval():
    eng = StockEngine(adjustment_approval_threshold=5)
    loc = eng.add_location("Stock", "WH1")
    p = eng.add_product("Steel", "STL-1", initial_stock=50, location_id=loc.id)
    center = AlertCenter()

    adj = eng.create_adjustment(loc.id, [(p.id, 0)], reason="lost", user="staff")
    with pytest.raises(ApprovalRequired):
        eng.validate(adj.id, user="staff")
    center.refresh(eng)
    assert [a.kind for a in center.list_alerts()] == ["approval_needed"]

    eng.approve(adj.id, user="manager")
    center.refresh(eng)
    assert center.list_alerts() == []


# ---------------- API ----------------
def test_service_endpoints():
    c = TestClient(create_app(StockEngine()))

    t = c.get("/api/import/products/template")
    assert t.status_code == 200 and "sku" in t.text

    r = c.post("/api/import/products", params={"dry_run": "false"},
               files={"file": ("items.csv", CSV, "text/csv")}, headers={"X-User": "manager"})
    assert r.status_code == 200 and r.json()["created"] == 2
    assert c.post("/api/import/products",
                  files={"file": ("x.pdf", b"1", "application/pdf")}).status_code == 400

    assert c.get("/api/reports/valuation").json()["total"] == 6500
    assert "text/csv" in c.get("/api/reports/export/stock.csv").headers["content-type"]
    assert c.get("/api/reports/movers").status_code == 200

    alerts = c.get("/api/alerts").json()
    assert any(a["kind"] == "out_of_stock" for a in alerts)
    c.post(f"/api/alerts/{alerts[0]['id']}/read")
    assert c.get("/api/alerts/count").json()["unread"] == len(alerts) - 1