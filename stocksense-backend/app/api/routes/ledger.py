from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import Engine
from app.engine.models import OpType
from app.schemas.operation import LedgerEntryOut

router = APIRouter(prefix="/ledger", tags=["Move History"])


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("", response_model=list[LedgerEntryOut])
def move_history(eng: Engine,
                 product_id: Optional[int] = None,
                 location_id: Optional[int] = None,
                 op_type: Optional[OpType] = Query(None, alias="type"),
                 user: Optional[str] = None,
                 since: Optional[datetime] = None,
                 until: Optional[datetime] = None,
                 limit: int = Query(200, ge=1, le=1000)):
    """Every stock movement, newest first."""
    entries = eng.move_history(product_id, location_id, op_type, user, _aware(since), _aware(until))
    return entries[:limit]