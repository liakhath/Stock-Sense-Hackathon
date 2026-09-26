from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, Engine
from app.engine import StockEngine
from app.engine.models import Operation, OpStatus, OpType
from app.schemas.operation import (
    AdjustmentCreate, DeliveryCreate, OperationOut, ReceiptCreate, ReverseRequest, TransferCreate,
)

router = APIRouter(prefix="/operations", tags=["Operations"])


def to_out(eng: StockEngine, op: Operation) -> OperationOut:
    """Convert and add product name/SKU to each line for display."""
    out = OperationOut.model_validate(op)
    for line in out.lines:
        p = eng.store.products.get(line.product_id)
        if p:
            line.product_name, line.sku = p.name, p.sku
    return out


# ---------- list / get ----------
@router.get("", response_model=list[OperationOut])
def list_operations(eng: Engine,
                    op_type: Optional[OpType] = Query(None, alias="type"),
                    status: Optional[OpStatus] = None,
                    warehouse: Optional[str] = None,
                    category: Optional[str] = None):
    """Dashboard filters: type, status, warehouse, product category. Newest first."""
    return [to_out(eng, o) for o in eng.list_operations(op_type, status, warehouse, category)]


@router.get("/{op_id}", response_model=OperationOut)
def get_operation(op_id: int, eng: Engine):
    return to_out(eng, eng._op(op_id))


# ---------- create ----------
@router.post("/receipts", response_model=OperationOut, status_code=201)
def create_receipt(body: ReceiptCreate, eng: Engine, user: CurrentUser):
    op = eng.create_receipt(body.location_id, body.engine_lines(), partner=body.partner,
                            user=user, note=body.note)
    return to_out(eng, op)


@router.post("/deliveries", response_model=OperationOut, status_code=201)
def create_delivery(body: DeliveryCreate, eng: Engine, user: CurrentUser):
    op = eng.create_delivery(body.location_id, body.engine_lines(), partner=body.partner,
                             user=user, note=body.note)
    return to_out(eng, op)


@router.post("/transfers", response_model=OperationOut, status_code=201)
def create_transfer(body: TransferCreate, eng: Engine, user: CurrentUser):
    op = eng.create_transfer(body.from_location_id, body.to_location_id, body.engine_lines(),
                             user=user, note=body.note)
    return to_out(eng, op)


@router.post("/adjustments", response_model=OperationOut, status_code=201)
def create_adjustment(body: AdjustmentCreate, eng: Engine, user: CurrentUser):
    op = eng.create_adjustment(body.location_id, body.engine_lines(), reason=body.reason,
                               user=user, note=body.note)
    return to_out(eng, op)


@router.post("/reorder", response_model=Optional[OperationOut], status_code=201)
def auto_reorder(location_id: int, eng: Engine, user: CurrentUser):
    """Draft ONE receipt for all low-stock products. Returns null if nothing needs reordering."""
    op = eng.create_reorder_receipts(location_id, user=user)
    return to_out(eng, op) if op else None


# ---------- workflow actions ----------
@router.post("/{op_id}/confirm", response_model=OperationOut)
def confirm(op_id: int, eng: Engine):
    return to_out(eng, eng.confirm(op_id))


@router.post("/{op_id}/check-availability", response_model=OperationOut)
def check_availability(op_id: int, eng: Engine):
    return to_out(eng, eng.check_availability(op_id))


@router.post("/{op_id}/validate", response_model=OperationOut)
def validate(op_id: int, eng: Engine, user: CurrentUser):
    return to_out(eng, eng.validate(op_id, user=user))


@router.post("/{op_id}/approve", response_model=OperationOut)
def approve(op_id: int, eng: Engine, user: CurrentUser):
    return to_out(eng, eng.approve(op_id, user=user))


@router.post("/{op_id}/cancel", response_model=OperationOut)
def cancel(op_id: int, eng: Engine, user: CurrentUser):
    return to_out(eng, eng.cancel(op_id, user=user))


@router.post("/{op_id}/reverse", response_model=OperationOut, status_code=201)
def reverse(op_id: int, eng: Engine, user: CurrentUser, body: Optional[ReverseRequest] = None):
    """Undo a done operation. Returns the NEW reversal operation."""
    return to_out(eng, eng.reverse(op_id, user=user, note=body.note if body else ""))