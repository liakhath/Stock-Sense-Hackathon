from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from .common import OutModel, Qty


class RowIssue(BaseModel):
    row: int
    message: str


class ImportReport(BaseModel):
    dry_run: bool
    total_rows: int
    created: int
    updated: int
    skipped: int
    errors: list[RowIssue]
    warnings: list[RowIssue]


class MoverItem(OutModel):
    product_id: int
    sku: str
    name: str
    category: str
    on_hand: Qty
    shipped: Qty
    received: Qty
    avg_daily: Qty
    days_of_cover: Optional[Qty] = None
    stock_value: Qty


class MoversOut(OutModel):
    days: int
    fast_movers: list[MoverItem]
    slow_movers: list[MoverItem]
    dead_stock: list[MoverItem]


class ValueRow(OutModel):
    name: str
    value: Qty


class ValuationOut(OutModel):
    total: Qty
    by_category: list[ValueRow]
    by_warehouse: list[ValueRow]


class AlertOut(OutModel):
    id: int
    kind: Literal["low_stock", "out_of_stock", "approval_needed"]
    message: str
    product_id: Optional[int] = None
    operation_id: Optional[int] = None
    created_at: datetime
    read: bool
    resolved_at: Optional[datetime] = None