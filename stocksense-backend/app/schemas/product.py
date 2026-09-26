from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .common import OutModel, Qty

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, examples=["Steel Rod"])
    sku: str = Field(min_length=1, examples=["STL-001"])
    category: str = "General"
    uom: str = Field("unit", examples=["kg", "unit", "box"])
    min_qty: Decimal = Field(Decimal("0"), ge=0, description="Reorder point")
    reorder_qty: Decimal = Field(Decimal("0"), ge=0, description="Qty to order when low")
    unit_cost: Decimal = Field(Decimal("0"), ge=0)
    initial_stock: Decimal = Field(Decimal("0"), ge=0)
    location_id: Optional[int] = Field(None, description="Required if initial_stock > 0")


class ProductUpdate(BaseModel):
    """Send only the fields you want to change."""
    name: Optional[str] = Field(None, min_length=1)
    sku: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    uom: Optional[str] = None
    min_qty: Optional[Decimal] = Field(None, ge=0)
    reorder_qty: Optional[Decimal] = Field(None, ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    active: Optional[bool] = None

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True)


class ProductOut(OutModel):
    id: int
    name: str
    sku: str
    category: str
    uom: str
    min_qty: Qty
    reorder_qty: Qty
    unit_cost: Qty
    active: bool


class ProductWithStock(ProductOut):
    """Used by product list / search."""
    on_hand: Qty
    available: Qty
    stock_status: StockStatus


class StockAtLocation(OutModel):
    location_id: int
    location: str
    warehouse: str
    on_hand: Qty
    reserved: Qty
    available: Qty


class ProductStockOut(OutModel):
    """Stock availability per location for one product."""
    product_id: int
    on_hand: Qty
    reserved: Qty
    available: Qty
    by_location: list[StockAtLocation]


class LowStockItem(OutModel):
    product_id: int
    sku: str
    name: str
    status: Literal["low_stock", "out_of_stock"]
    available: Qty
    min_qty: Qty
    incoming: Qty
    suggested_order_qty: Qty
    days_of_cover: Optional[Qty] = None