from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import Engine
from app.engine.models import OpType
from app.schemas.reports import MoversOut, ValuationOut
from app.services import analytics

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


def _csv(text: str, filename: str) -> Response:
    # BOM so Excel opens UTF-8 correctly
    return Response("\ufeff" + text, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/movers", response_model=MoversOut)
def movers(eng: Engine, days: int = Query(30, ge=1, le=365), top: int = Query(5, ge=1, le=50)):
    """Fast movers, slow movers and dead stock over the last N days."""
    return analytics.movers(eng, days, top)


@router.get("/valuation", response_model=ValuationOut)
def valuation(eng: Engine):
    """Inventory value (on hand x unit cost), total + by category + by warehouse."""
    return analytics.valuation(eng)


@router.get("/export/stock.csv")
def export_stock(eng: Engine):
    return _csv(analytics.stock_csv(eng), "stock_report.csv")


@router.get("/export/ledger.csv")
def export_ledger(eng: Engine, product_id: Optional[int] = None,
                  op_type: Optional[OpType] = Query(None, alias="type"),
                  user: Optional[str] = None):
    entries = eng.move_history(product_id=product_id, op_type=op_type, user=user)
    return _csv(analytics.ledger_csv(eng, entries), "move_history.csv")