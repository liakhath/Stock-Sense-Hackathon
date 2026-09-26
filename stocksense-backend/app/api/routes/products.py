from typing import Optional

from fastapi import APIRouter

from app.api.deps import CurrentUser, Engine
from app.schemas.product import (
    LowStockItem, ProductCreate, ProductOut, ProductStockOut, ProductUpdate,
    ProductWithStock, StockStatus,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductWithStock])
def search_products(eng: Engine, q: Optional[str] = None, category: Optional[str] = None,
                    warehouse: Optional[str] = None, stock_status: Optional[StockStatus] = None,
                    include_archived: bool = False):
    """Search by name/SKU (partial) + filters. Exact SKU match comes first."""
    return eng.search_products(q, category, warehouse, stock_status, include_archived)


# --- fixed paths must come BEFORE /{product_id} ---
@router.get("/categories", response_model=list[str])
def list_categories(eng: Engine):
    return eng.list_categories()


@router.get("/low-stock", response_model=list[LowStockItem])
def low_stock(eng: Engine):
    """Low / out-of-stock products with suggested reorder qty and days of cover."""
    return eng.low_stock()


@router.get("/sku/{sku}", response_model=ProductOut)
def get_by_sku(sku: str, eng: Engine):
    """Barcode / SKU scan lookup."""
    return ProductOut.model_validate(eng.get_product_by_sku(sku))


@router.post("", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate, eng: Engine, user: CurrentUser):
    return ProductOut.model_validate(eng.add_product(**body.model_dump(), user=user))


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, eng: Engine):
    return ProductOut.model_validate(eng.get_product(product_id))


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, body: ProductUpdate, eng: Engine, user: CurrentUser):
    """Send only the fields to change. `{"active": false}` archives the product."""
    return ProductOut.model_validate(eng.update_product(product_id, user=user, **body.changes()))


@router.get("/{product_id}/stock", response_model=ProductStockOut)
def product_stock(product_id: int, eng: Engine):
    """Stock availability per location."""
    return eng.stock_of(product_id)