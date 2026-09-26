from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

# Decimal inside Python (exact math), plain number in JSON (easy for the frontend)
Qty = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class OutModel(BaseModel):
    """Base for responses: can be built straight from engine objects."""
    model_config = ConfigDict(from_attributes=True)