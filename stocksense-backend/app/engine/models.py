from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


def now() -> datetime:
    return datetime.now(timezone.utc)


def to_qty(value) -> Decimal:
    """Convert int/float/str to Decimal safely (avoids float rounding bugs with kg etc.)."""
    return Decimal(str(value))


class OpType(str, Enum):
    RECEIPT = "receipt"
    DELIVERY = "delivery"
    INTERNAL = "internal"
    ADJUSTMENT = "adjustment"


class OpStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"


class AdjustReason(str, Enum):
    COUNT_CORRECTION = "count_correction"
    DAMAGED = "damaged"
    LOST = "lost"
    THEFT = "theft"
    EXPIRED = "expired"
    OTHER = "other"


@dataclass
class Product:
    id: int
    name: str
    sku: str
    category: str = "General"
    uom: str = "unit"
    min_qty: Decimal = Decimal("0")      # reorder point: alert at or below this
    reorder_qty: Decimal = Decimal("0")  # how much to order when low
    unit_cost: Decimal = Decimal("0")    # used for inventory value


@dataclass
class Location:
    id: int
    name: str        # e.g. "Rack A", "Production Floor"
    warehouse: str   # e.g. "Main Warehouse"


@dataclass
class Quant:
    """Stock of one product at one location."""
    on_hand: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")

    @property
    def available(self) -> Decimal:
        return self.on_hand - self.reserved


@dataclass
class OperationLine:
    product_id: int
    qty: Decimal  # for adjustments this is the COUNTED quantity


@dataclass
class Operation:
    id: int
    ref: str                                  # e.g. WH/IN/0001
    type: OpType
    lines: list[OperationLine]
    src_location_id: Optional[int] = None     # None = outside (vendor)
    dst_location_id: Optional[int] = None     # None = outside (customer)
    partner: Optional[str] = None             # supplier or customer name
    reason: Optional[AdjustReason] = None     # adjustments only
    note: str = ""
    status: OpStatus = OpStatus.DRAFT
    created_by: str = "system"
    created_at: datetime = field(default_factory=now)
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    needs_approval: bool = False
    approved_by: Optional[str] = None
    reverses_id: Optional[int] = None         # set on a reversal operation
    reversed_by_id: Optional[int] = None      # set on the original once reversed


@dataclass
class LedgerEntry:
    id: int
    timestamp: datetime
    product_id: int
    qty: Decimal
    from_location_id: Optional[int]   # None = came from outside
    to_location_id: Optional[int]     # None = left the company
    operation_id: int
    operation_ref: str
    operation_type: OpType
    user: str                         # who did it (audit trail)