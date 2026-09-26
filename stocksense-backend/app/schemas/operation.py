from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.engine.models import AdjustReason, OpStatus, OpType

from .common import OutModel, Qty


# ---------- requests ----------
class LineIn(BaseModel):
    product_id: int
    qty: Decimal = Field(ge=0, description="For adjustments: the counted quantity")


class _WithLines(BaseModel):
    lines: list[LineIn] = Field(min_length=1)
    note: str = ""

    def engine_lines(self) -> list[tuple[int, Decimal]]:
        return [(l.product_id, l.qty) for l in self.lines]


class ReceiptCreate(_WithLines):
    location_id: int = Field(description="Where the goods arrive")
    partner: Optional[str] = Field(None, examples=["Tata Steel"])


class DeliveryCreate(_WithLines):
    location_id: int = Field(description="Where the goods leave from")
    partner: Optional[str] = Field(None, examples=["Customer A"])


class TransferCreate(_WithLines):
    from_location_id: int
    to_location_id: int


class AdjustmentCreate(_WithLines):
    location_id: int
    reason: AdjustReason


class ReverseRequest(BaseModel):
    note: str = ""


# ---------- responses ----------
class LineOut(OutModel):
    product_id: int
    qty: Qty
    product_name: Optional[str] = None   # filled by the route for display
    sku: Optional[str] = None


class OperationOut(OutModel):
    id: int
    ref: str
    type: OpType
    status: OpStatus
    lines: list[LineOut]
    src_location_id: Optional[int] = None
    dst_location_id: Optional[int] = None
    partner: Optional[str] = None
    reason: Optional[AdjustReason] = None
    note: str = ""
    created_by: str
    created_at: datetime
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    needs_approval: bool = False
    approved_by: Optional[str] = None
    reverses_id: Optional[int] = None
    reversed_by_id: Optional[int] = None


class LedgerEntryOut(OutModel):
    id: int
    timestamp: datetime
    product_id: int
    qty: Qty
    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None
    operation_id: int
    operation_ref: str
    operation_type: OpType
    user: str