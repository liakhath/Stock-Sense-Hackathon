from decimal import Decimal

import pytest

from app.engine import (
    ApprovalRequired, InsufficientStock, InvalidOperation, NotFound, OpStatus, StockEngine,
)


@pytest.fixture
def env():
    eng = StockEngine(adjustment_approval_threshold=10)
    main = eng.add_location("Main Store", "WH1")
    rack = eng.add_location("Production Rack", "WH1")
    steel = eng.add_product("Steel", "STL-001", category="Raw", uom="kg",
                            min_qty=20, reorder_qty=100, unit_cost=50)
    return eng, main, rack, steel


def test_prd_example_flow(env):
    eng, main, rack, steel = env
    r = eng.create_receipt(main.id, [(steel.id, 100)], partner="Vendor", user="manager")
    eng.validate(r.id, user="manager")
    assert eng.total_on_hand(steel.id) == 100

    t = eng.create_transfer(main.id, rack.id, [(steel.id, 100)], user="staff")
    eng.validate(t.id, user="staff")
    assert eng.total_on_hand(steel.id) == 100
    assert eng.quant_at(steel.id, rack.id).on_hand == 100

    d = eng.create_delivery(rack.id, [(steel.id, 20)], partner="Customer", user="staff")
    eng.validate(d.id, user="staff")

    a = eng.create_adjustment(rack.id, [(steel.id, 77)], reason="damaged", user="staff")
    eng.validate(a.id, user="staff")

    assert eng.total_on_hand(steel.id) == 77
    assert len(eng.move_history(product_id=steel.id)) == 4
    assert eng.move_history()[0].user == "staff"


def test_cannot_deliver_more_than_stock(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 5)]).id)
    d = eng.create_delivery(main.id, [(steel.id, 10)])
    with pytest.raises(InsufficientStock):
        eng.validate(d.id)
    assert d.status is OpStatus.WAITING
    assert eng.total_on_hand(steel.id) == 5


def test_reservation_blocks_double_booking(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 10)]).id)
    d1 = eng.confirm(eng.create_delivery(main.id, [(steel.id, 10)]).id)
    d2 = eng.confirm(eng.create_delivery(main.id, [(steel.id, 5)]).id)
    assert d1.status is OpStatus.READY
    assert d2.status is OpStatus.WAITING
    eng.cancel(d1.id)
    assert eng.check_availability(d2.id).status is OpStatus.READY


def test_large_adjustment_needs_approval(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 100)]).id)
    a = eng.create_adjustment(main.id, [(steel.id, 50)], reason="lost", user="staff")
    with pytest.raises(ApprovalRequired):
        eng.validate(a.id, user="staff")
    with pytest.raises(InvalidOperation):
        eng.approve(a.id, user="staff")  # can't approve own
    eng.approve(a.id, user="manager")
    eng.validate(a.id, user="staff")
    assert eng.total_on_hand(steel.id) == 50


def test_adjustment_requires_reason(env):
    eng, main, _, steel = env
    with pytest.raises(InvalidOperation):
        eng.create_adjustment(main.id, [(steel.id, 5)], reason="")


def test_reverse(env):
    eng, main, _, steel = env
    r = eng.validate(eng.create_receipt(main.id, [(steel.id, 10)]).id)
    rev = eng.reverse(r.id, user="manager")
    assert eng.total_on_hand(steel.id) == 0
    assert rev.reverses_id == r.id
    with pytest.raises(InvalidOperation):
        eng.reverse(r.id)


def test_low_stock_and_auto_reorder(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 15)]).id)
    low = eng.low_stock()
    assert low[0]["status"] == "low_stock"
    assert low[0]["suggested_order_qty"] == 100
    draft = eng.create_reorder_receipts(main.id)
    assert draft is not None and draft.status is OpStatus.DRAFT
    assert eng.create_reorder_receipts(main.id) is None  # already covered by incoming


def test_dashboard_kpis(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 10)]).id)
    eng.create_delivery(main.id, [(steel.id, 2)])
    k = eng.dashboard_kpis()
    assert k["total_products_in_stock"] == 1
    assert k["low_stock_items"] == 1
    assert k["pending_deliveries"] == 1
    assert k["inventory_value"] == 500

def test_update_product(env):
    eng, main, _, steel = env
    eng.add_product("Copper", "CU-1")
    p = eng.update_product(steel.id, name="Steel Rod", min_qty=30, reorder_qty="150.5")
    assert p.name == "Steel Rod" and p.min_qty == 30 and p.reorder_qty == Decimal("150.5")
    with pytest.raises(InvalidOperation):
        eng.update_product(steel.id, sku="cu-1")        # duplicate SKU
    with pytest.raises(InvalidOperation):
        eng.update_product(steel.id, min_qty=-1)        # negative
    with pytest.raises(InvalidOperation):
        eng.update_product(steel.id, colour="red")      # unknown field
    eng.update_product(steel.id, uom="ton")             # OK: no stock moved yet
    eng.validate(eng.create_receipt(main.id, [(steel.id, 1)]).id)
    with pytest.raises(InvalidOperation):
        eng.update_product(steel.id, uom="kg")          # locked after history


def test_archive_product(env):
    eng, main, _, steel = env
    eng.validate(eng.create_receipt(main.id, [(steel.id, 10)]).id)
    with pytest.raises(InvalidOperation):
        eng.update_product(steel.id, active=False)      # still has stock
    eng.validate(eng.create_delivery(main.id, [(steel.id, 10)]).id)
    eng.update_product(steel.id, active=False)
    assert eng.search_products("steel") == []
    assert len(eng.search_products("steel", include_archived=True)) == 1
    with pytest.raises(InvalidOperation):
        eng.create_receipt(main.id, [(steel.id, 1)])


def test_search_products(env):
    eng, main, _, steel = env
    eng.add_product("Steel Bolt", "BLT-9", category="Hardware", min_qty=5)
    chair = eng.add_product("Chair", "CHR-1", category="Furniture")
    shelf = eng.add_location("Shelf 1", "WH2")
    eng.validate(eng.create_receipt(main.id, [(steel.id, 100)]).id)
    eng.validate(eng.create_receipt(shelf.id, [(chair.id, 3)]).id)

    assert {r["name"] for r in eng.search_products("steel")} == {"Steel", "Steel Bolt"}
    assert eng.search_products("blt-9")[0]["sku"] == "BLT-9"
    assert [r["name"] for r in eng.search_products(category="furniture")] == ["Chair"]
    assert [r["name"] for r in eng.search_products(warehouse="WH2")] == ["Chair"]
    assert [r["name"] for r in eng.search_products(stock_status="out_of_stock")] == ["Steel Bolt"]
    assert eng.list_categories() == ["Furniture", "Hardware", "Raw"]


def test_get_product_by_sku(env):
    eng, _, _, steel = env
    assert eng.get_product_by_sku(" stl-001 ").id == steel.id
    with pytest.raises(NotFound):
        eng.get_product_by_sku("NOPE")