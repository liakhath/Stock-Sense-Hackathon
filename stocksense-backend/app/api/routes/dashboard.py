from fastapi import APIRouter

from app.api.deps import Engine
from app.schemas.dashboard import KpisOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KpisOut)
def kpis(eng: Engine):
    return eng.dashboard_kpis()