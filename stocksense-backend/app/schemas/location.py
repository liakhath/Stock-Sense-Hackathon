from pydantic import BaseModel, Field

from .common import OutModel


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, examples=["Rack A"])
    warehouse: str = Field(min_length=1, examples=["Main Warehouse"])


class LocationOut(OutModel):
    id: int
    name: str
    warehouse: str