from __future__ import annotations

from collections import defaultdict
from itertools import count

from .models import LedgerEntry, Location, Operation, Product, Quant


class InMemoryStore:
    """Temporary storage. Later we replace this with a DB-backed store
    that has the same attributes/methods, so the engine doesn't change."""

    def __init__(self) -> None:
        self.products: dict[int, Product] = {}
        self.locations: dict[int, Location] = {}
        self.quants: dict[tuple[int, int], Quant] = {}   # (product_id, location_id) -> Quant
        self.operations: dict[int, Operation] = {}
        self.ledger: list[LedgerEntry] = []
        self._ids = defaultdict(lambda: count(1))

    def next_id(self, kind: str) -> int:
        return next(self._ids[kind])

    def quant(self, product_id: int, location_id: int) -> Quant:
        key = (product_id, location_id)
        if key not in self.quants:
            self.quants[key] = Quant()
        return self.quants[key]