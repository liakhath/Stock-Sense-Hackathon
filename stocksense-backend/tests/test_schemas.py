from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.engine import StockEngine
from app.schemas.dashboard import KpisOut
from app.schemas.operation import AdjustmentCreate, LedgerEntryOut, OperationOut, ReceiptCreate
from app.schemas.product import (
    LowStockItem, ProductCreate, ProductOut, ProductStockOut, ProductUpdate, ProductWithStock,
)


def test_engine_objects_convert_to_json():
    eng = StockEngine()
    loc = eng.add_location("Main", "WH1")
    p = eng.add_product("Steel", "STL-1", uom="kg", min_qty=20, unit_cost="2.5")

    body = ReceiptCreate(location_id=loc.id, lines=[{"product_id": p.id, "qty": "10.5"}], partner="V")
    op = eng.create_receipt(body.location_id, body.engine_lines(), partner=body.partner)
    eng.validate(op.id)

    out = OperationOut.model_validate(op).model_dump(mode="json")
    assert out["ref"] == "WH/IN/0001" and out["status"] == "done"
    assert out["lines"][0]["qty"] == 10.5                      # number, not string
    assert ProductOut.model_validate(p).model_dump(mode="json")["unit_cost"] == 2.5
    assert ProductWithStock.model_validate(eng.search_products()[0]).stock_status == "low_stock"
    ProductStockOut.model_validate(eng.stock_of(p.id))
    LowStockItem.model_validate(eng.low_stock()[0])
    LedgerEntryOut.model_validate(eng.move_history()[0])
    assert KpisOut.model_validate(eng.dashboard_kpis()).low_stock_items == 1


def test_product_update_sends_only_changed_fields():
    assert ProductUpdate(min_qty=5).changes() == {"min_qty": Decimal("5")}


def test_bad_input_is_rejected():
    with pytest.raises(ValidationError):
        ReceiptCreate(location_id=1, lines=[])                   # no lines
    with pytest.raises(ValidationError):
        ProductCreate(name="", sku="X")                          # empty name
    with pytest.raises(ValidationError):
        AdjustmentCreate(location_id=1, lines=[{"product_id": 1, "qty": 1}], reason="bored")
    with pytest.raises(ValidationError):
        ReceiptCreate(location_id=1, lines=[{"product_id": 1, "qty": -5}])