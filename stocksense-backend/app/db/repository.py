"""Database-backed store.

The engine keeps working on fast in-memory objects exactly like before.
PersistentStore adds two things:
  - load(): on startup, read everything from the database into memory
  - save(): after each change, write ONLY what changed (dirty tracking) in one transaction
So the engine, routes and services don't change at all.
"""
from __future__ import annotations

import threading
from datetime import timezone
from itertools import count
from typing import Union

from sqlalchemy import select
from sqlalchemy.engine import Engine

from app.engine.models import (
    AdjustReason, LedgerEntry, Location, Operation, OperationLine, OpStatus, OpType, Product, Quant,
)
from app.engine.store import InMemoryStore

from . import tables as t
from .database import make_engine


def _aware(dt):
    """SQLite drops timezone info; Postgres keeps it. Always return UTC-aware datetimes."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class PersistentStore(InMemoryStore):
    def __init__(self, url_or_engine: Union[str, Engine]) -> None:
        super().__init__()
        self.db = make_engine(url_or_engine) if isinstance(url_or_engine, str) else url_or_engine
        self._saved: dict = {"locations": {}, "products": {}, "quants": {}, "operations": {}}
        self._saved_ledger_len = 0
        self._save_lock = threading.Lock()

    # ------------------------------------------------------------------ schema
    def create_schema(self) -> None:
        t.metadata.create_all(self.db)

    def drop_schema(self) -> None:
        t.metadata.drop_all(self.db)

    # ------------------------------------------------------------------ load
    def load(self) -> "PersistentStore":
        self.create_schema()
        with self.db.connect() as c:
            for r in c.execute(select(t.locations)).mappings():
                self.locations[r["id"]] = Location(id=r["id"], name=r["name"], warehouse=r["warehouse"])

            for r in c.execute(select(t.products)).mappings():
                self.products[r["id"]] = Product(
                    id=r["id"], name=r["name"], sku=r["sku"], category=r["category"], uom=r["uom"],
                    min_qty=r["min_qty"], reorder_qty=r["reorder_qty"], unit_cost=r["unit_cost"],
                    active=r["active"],
                )

            for r in c.execute(select(t.stock_quants)).mappings():
                self.quants[(r["product_id"], r["location_id"])] = Quant(
                    on_hand=r["on_hand"], reserved=r["reserved"])

            lines: dict = {}
            q = select(t.operation_lines).order_by(t.operation_lines.c.operation_id,
                                                   t.operation_lines.c.line_no)
            for r in c.execute(q).mappings():
                lines.setdefault(r["operation_id"], []).append(
                    OperationLine(product_id=r["product_id"], qty=r["qty"]))

            for r in c.execute(select(t.operations).order_by(t.operations.c.id)).mappings():
                self.operations[r["id"]] = Operation(
                    id=r["id"], ref=r["ref"], type=OpType(r["type"]), status=OpStatus(r["status"]),
                    lines=lines.get(r["id"], []),
                    src_location_id=r["src_location_id"], dst_location_id=r["dst_location_id"],
                    partner=r["partner"], reason=AdjustReason(r["reason"]) if r["reason"] else None,
                    note=r["note"] or "", created_by=r["created_by"],
                    created_at=_aware(r["created_at"]), validated_by=r["validated_by"],
                    validated_at=_aware(r["validated_at"]), needs_approval=r["needs_approval"],
                    approved_by=r["approved_by"], reverses_id=r["reverses_id"],
                    reversed_by_id=r["reversed_by_id"],
                )

            for r in c.execute(select(t.stock_ledger).order_by(t.stock_ledger.c.id)).mappings():
                self.ledger.append(LedgerEntry(
                    id=r["id"], timestamp=_aware(r["timestamp"]), product_id=r["product_id"],
                    qty=r["qty"], from_location_id=r["from_location_id"],
                    to_location_id=r["to_location_id"], operation_id=r["operation_id"],
                    operation_ref=r["operation_ref"], operation_type=OpType(r["operation_type"]),
                    user=r["user_name"],
                ))

        self._reset_counters()
        self._saved = self._rows()
        self._saved_ledger_len = len(self.ledger)
        return self

    def _reset_counters(self) -> None:
        """Continue IDs and refs (WH/IN/0007 ...) after the highest ones already in the DB."""
        def resume(kind: str, highest: int) -> None:
            self._ids[kind] = count(highest + 1)

        resume("location", max(self.locations, default=0))
        resume("product", max(self.products, default=0))
        resume("operation", max(self.operations, default=0))
        resume("ledger", max((e.id for e in self.ledger), default=0))
        for op_type in OpType:
            seqs = [int(o.ref.rsplit("/", 1)[-1]) for o in self.operations.values()
                    if o.type is op_type and o.ref.rsplit("/", 1)[-1].isdigit()]
            resume(f"ref:{op_type.value}", max(seqs, default=0))

    # ------------------------------------------------------------------ save
    def _rows(self) -> dict:
        return {
            "locations": {
                l.id: {"id": l.id, "name": l.name, "warehouse": l.warehouse}
                for l in self.locations.values()
            },
            "products": {
                p.id: {"id": p.id, "name": p.name, "sku": p.sku, "category": p.category,
                       "uom": p.uom, "min_qty": p.min_qty, "reorder_qty": p.reorder_qty,
                       "unit_cost": p.unit_cost, "active": p.active}
                for p in self.products.values()
            },
            "quants": {
                key: {"product_id": key[0], "location_id": key[1],
                      "on_hand": q.on_hand, "reserved": q.reserved}
                for key, q in self.quants.items()
            },
            "operations": {
                o.id: {"id": o.id, "ref": o.ref, "type": o.type.value, "status": o.status.value,
                       "src_location_id": o.src_location_id, "dst_location_id": o.dst_location_id,
                       "partner": o.partner, "reason": o.reason.value if o.reason else None,
                       "note": o.note or "", "created_by": o.created_by, "created_at": o.created_at,
                       "validated_by": o.validated_by, "validated_at": o.validated_at,
                       "needs_approval": o.needs_approval, "approved_by": o.approved_by,
                       "reverses_id": o.reverses_id, "reversed_by_id": o.reversed_by_id}
                for o in self.operations.values()
            },
        }

    def save(self) -> int:
        """Write everything that changed since the last save. Returns number of rows written.
        All-or-nothing: if the DB write fails, nothing is marked saved and the next save retries."""
        with self._save_lock:
            rows = self._rows()
            changed = {name: [r for key, r in rows[name].items() if self._saved[name].get(key) != r]
                       for name in rows}
            new_op_ids = [oid for oid in rows["operations"] if oid not in self._saved["operations"]]
            new_lines = [
                {"operation_id": oid, "line_no": i, "product_id": l.product_id, "qty": l.qty}
                for oid in new_op_ids
                for i, l in enumerate(self.operations[oid].lines, start=1)
            ]
            new_ledger = [
                {"id": e.id, "timestamp": e.timestamp, "product_id": e.product_id, "qty": e.qty,
                 "from_location_id": e.from_location_id, "to_location_id": e.to_location_id,
                 "operation_id": e.operation_id, "operation_ref": e.operation_ref,
                 "operation_type": e.operation_type.value, "user_name": e.user}
                for e in self.ledger[self._saved_ledger_len:]
            ]
            written = sum(len(v) for v in changed.values()) + len(new_lines) + len(new_ledger)
            if written == 0:
                return 0

            with self.db.begin() as c:          # one transaction; order respects foreign keys
                self._upsert(c, t.locations, changed["locations"], ["id"])
                self._upsert(c, t.products, changed["products"], ["id"])
                self._upsert(c, t.stock_quants, changed["quants"], ["product_id", "location_id"])
                self._upsert(c, t.operations, changed["operations"], ["id"])
                if new_lines:
                    c.execute(t.operation_lines.insert(), new_lines)
                if new_ledger:
                    c.execute(t.stock_ledger.insert(), new_ledger)

            self._saved = rows
            self._saved_ledger_len = len(self.ledger)
            return written

    @staticmethod
    def _upsert(conn, table, rows: list, keys: list) -> None:
        if not rows:
            return
        if conn.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        elif conn.dialect.name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise RuntimeError(f"Unsupported database: {conn.dialect.name}")
        stmt = insert(table)
        update = {c.name: stmt.excluded[c.name] for c in table.columns if c.name not in keys}
        conn.execute(stmt.on_conflict_do_update(index_elements=keys, set_=update), rows)
