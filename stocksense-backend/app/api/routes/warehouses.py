from typing import Optional

from fastapi import APIRouter

from app.api.deps import Engine, Manager
from app.schemas.location import LocationCreate, LocationOut

router = APIRouter(tags=["Warehouses & Locations"])


@router.get("/warehouses", response_model=list[str])
def list_warehouses(eng: Engine):
    return sorted({loc.warehouse for loc in eng.store.locations.values()})


@router.get("/locations", response_model=list[LocationOut])
def list_locations(eng: Engine, warehouse: Optional[str] = None):
    locs = eng.store.locations.values()
    if warehouse:
        locs = [l for l in locs if l.warehouse == warehouse]
    return sorted(locs, key=lambda l: (l.warehouse, l.name))


@router.post("/locations", response_model=LocationOut, status_code=201)
def create_location(body: LocationCreate, eng: Engine, _: Manager):
    """Managers only."""
    return eng.add_location(body.name, body.warehouse)