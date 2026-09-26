"""StockSense stock engine.

Every stock change goes through an Operation (receipt, delivery, internal
transfer, adjustment). Validating an operation turns it into moves, and every
move is written to the stock ledger along with the user who made it.

Status flow:  DRAFT -> (confirm) -> WAITING / READY -> (validate) -> DONE
              any status except DONE -> (cancel) -> CANCELED
              DONE -> (reverse) -> creates a new DONE operation that undoes it
"""
from __future__ import annotations

import threading
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import Iterable, Optional
from dataclasses import asdict

from .errors import ApprovalRequired, InsufficientStock, InvalidOperation, NotFound
from .models import (
    AdjustReason, LedgerEntry, Location, Operation, OperationLine,
    OpStatus, OpType, Product, Quant, now, to_qty,
)
from .store import InMemoryStore

ZERO = Decimal("0")
REF_PREFIX = {
    OpType.RECEIPT: "IN",
    OpType.DELIVERY: "OUT",
    OpType.INTERNAL: "INT",
    OpType.ADJUSTMENT: "ADJ",
}
OPEN_STATUSES = (OpStatus.DRAFT, OpStatus.WAITING, OpStatus.READY)
RESERVING_TYPES = (OpType.DELIVERY, OpType.INTERNAL)
PRODUCT_FIELDS = {"name", "sku", "category", "uom", "min_qty", "reorder_qty", "unit_cost", "active"}

# (product_id, from_location_id, to_location_id, qty); None = outside the company
Move = tuple[int, Optional[int], Optional[int], Decimal]
LineInput = Iterable[tuple]  # [(product_id, qty), ...]


class StockEngine:
    def __init__(self, store: Optional[InMemoryStore] = None,
                 adjustment_approval_threshold=None) -> None:
        """adjustment_approval_threshold: if set, any adjustment that changes a
        product's stock by more than this many units needs a manager's approval."""
        self.store = store or InMemoryStore()
        self.approval_threshold = (
            to_qty(adjustment_approval_threshold)
            if adjustment_approval_threshold is not None else None
        )
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ master data
    def add_location(self, name: str, warehouse: str) -> Location:
        with self._lock:
            loc = Location(id=self.store.next_id("location"), name=name, warehouse=warehouse)
            self.store.locations[loc.id] = loc
            return loc

    def add_product(self, name: str, sku: str, category: str = "General", uom: str = "unit",
                    min_qty=0, reorder_qty=0, unit_cost=0, initial_stock=0,
                    location_id: Optional[int] = None, user: str = "system") -> Product:
        with self._lock:
            if any(p.sku.lower() == sku.lower() for p in self.store.products.values()):
                raise InvalidOperation(f"SKU '{sku}' already exists")
            p = Product(
                id=self.store.next_id("product"), name=name, sku=sku, category=category,
                uom=uom, min_qty=to_qty(min_qty), reorder_qty=to_qty(reorder_qty),
                unit_cost=to_qty(unit_cost),
            )
            self.store.products[p.id] = p
            if to_qty(initial_stock) > 0:
                if location_id is None:
                    raise InvalidOperation("location_id is required when setting initial stock")
                op = self.create_receipt(location_id, [(p.id, initial_stock)],
                                         partner="Initial stock", user=user)
                self.validate(op.id, user=user)
            return p
                            
    def get_product(self, product_id: int) -> Product:
        return self._product(product_id)

    def get_product_by_sku(self, sku: str) -> Product:
        """Exact SKU lookup (case-insensitive). Used for barcode scans."""
        term = sku.strip().lower()
        for p in self.store.products.values():
            if p.sku.lower() == term:
                return p
        raise NotFound(f"No product with SKU '{sku}'")

    def update_product(self, product_id: int, user: str = "system", **changes) -> Product:
        """Update product details and reorder rules.
        Allowed fields: name, sku, category, uom, min_qty, reorder_qty, unit_cost, active.
        `user` is accepted now so the API can pass it; the DB step will log it."""
        with self._lock:
            p = self._product(product_id)

            unknown = set(changes) - PRODUCT_FIELDS
            if unknown:
                raise InvalidOperation(f"Can't update: {', '.join(sorted(unknown))}")

            if "name" in changes:
                changes["name"] = str(changes["name"]).strip()
                if not changes["name"]:
                    raise InvalidOperation("Name can't be empty")

            if "sku" in changes:
                sku = str(changes["sku"]).strip()
                if not sku:
                    raise InvalidOperation("SKU can't be empty")
                if any(o.id != p.id and o.sku.lower() == sku.lower()
                       for o in self.store.products.values()):
                    raise InvalidOperation(f"SKU '{sku}' already exists")
                changes["sku"] = sku

            for f in ("min_qty", "reorder_qty", "unit_cost"):
                if f in changes:
                    changes[f] = to_qty(changes[f])
                    if changes[f] < 0:
                        raise InvalidOperation(f"{f} can't be negative")

            if "uom" in changes and changes["uom"] != p.uom and self._has_history(p.id):
                raise InvalidOperation("Unit of measure can't change after stock has moved")

            if changes.get("active") is False and p.active:
                if self.total_on_hand(p.id) != 0:
                    raise InvalidOperation("Can't archive a product that still has stock")
                if self._has_open_operations(p.id):
                    raise InvalidOperation("Can't archive a product used in open operations")

            for field_name, value in changes.items():
                setattr(p, field_name, value)
            return p

    def search_products(self, query: Optional[str] = None, category: Optional[str] = None,
                        warehouse: Optional[str] = None, stock_status: Optional[str] = None,
                        include_archived: bool = False) -> list[dict]:
        """Search by name or SKU (partial match) with filters.
        stock_status: 'in_stock' | 'low_stock' | 'out_of_stock'.
        An exact SKU match is always listed first."""
        term = (query or "").strip().lower()
        results = []
        for p in self.store.products.values():
            if not include_archived and not p.active:
                continue
            if term and term not in p.name.lower() and term not in p.sku.lower():
                continue
            if category and p.category.lower() != category.lower():
                continue
            if warehouse and not any(
                    pid == p.id and q.on_hand > 0
                    and self.store.locations[lid].warehouse == warehouse
                    for (pid, lid), q in self.store.quants.items()):
                continue
            available = self._total(p.id, "available")
            status = self._stock_status(p, available)
            if stock_status and status != stock_status:
                continue
            results.append({
                **asdict(p),
                "on_hand": self._total(p.id, "on_hand"),
                "available": available,
                "stock_status": status,
            })
        results.sort(key=lambda r: (r["sku"].lower() != term, r["name"].lower()))
        return results

    def list_categories(self) -> list[str]:
        return sorted({p.category for p in self.store.products.values() if p.active})

    def list_products(self, active: Optional[bool] = True) -> list[Product]:
        """If active is None, return all products; otherwise return active/inactive."""
        with self._lock:
            if active is None:
                return list(self.store.products.values())
            return [p for p in self.store.products.values() if p.active == active]

    def archive_product(self, product_id: int) -> Product:
        return self.update_product(product_id, active=False)

    def unarchive_product(self, product_id: int) -> Product:
        return self.update_product(product_id, active=True)

    def product_is_archived(self, product_id: int) -> bool:
        return self.store.products[product_id].active is False

    def list_locations(self) -> list[Location]:
        with self._lock:
            return list(self.store.locations.values())

    def get_location(self, location_id: int) -> Location:
        loc = self.store.locations.get(location_id)
        if loc is None:
            raise NotFound(f"Location {location_id} not found")
        return loc

    def update_location(self, location_id: int, **changes: object) -> Location:
        with self._lock:
            loc = self.get_location(location_id)
            for k, v in changes.items():
                if k not in ("name", "warehouse"):
                    raise InvalidOperation(f"Field '{k}' cannot be updated")
                setattr(loc, k, v)
            return loc

            
    # ------------------------------------------------------------------ create operations
    def create_receipt(self, location_id: int, lines: LineInput, partner: Optional[str] = None,
                       user: str = "system", note: str = "") -> Operation:
        """Goods arriving from a vendor into location_id."""
        return self._create(OpType.RECEIPT, lines, dst=location_id,
                            partner=partner, user=user, note=note)

    def create_delivery(self, location_id: int, lines: LineInput, partner: Optional[str] = None,
                        user: str = "system", note: str = "") -> Operation:
        """Goods leaving location_id to a customer."""
        return self._create(OpType.DELIVERY, lines, src=location_id,
                            partner=partner, user=user, note=note)

    def create_transfer(self, from_location_id: int, to_location_id: int, lines: LineInput,
                        user: str = "system", note: str = "") -> Operation:
        """Move stock between two internal locations."""
        if from_location_id == to_location_id:
            raise InvalidOperation("Source and destination must be different")
        return self._create(OpType.INTERNAL, lines, src=from_location_id,
                            dst=to_location_id, user=user, note=note)

    def create_adjustment(self, location_id: int, counts: LineInput, reason,
                          user: str = "system", note: str = "") -> Operation:
        """counts = [(product_id, counted_qty)]. Stock is set to the counted qty on validate."""
        try:
            reason = AdjustReason(reason)
        except ValueError:
            valid = ", ".join(r.value for r in AdjustReason)
            raise InvalidOperation(f"Reason is required. Use one of: {valid}")
        return self._create(OpType.ADJUSTMENT, counts, dst=location_id,
                            reason=reason, user=user, note=note)

    # ------------------------------------------------------------------ status workflow
    def confirm(self, op_id: int) -> Operation:
        """DRAFT -> READY (or WAITING if stock isn't available yet)."""
        with self._lock:
            op = self._op(op_id)
            if op.status is not OpStatus.DRAFT:
                raise InvalidOperation(f"{op.ref} is {op.status.value}; only drafts can be confirmed")
            if op.type in RESERVING_TYPES:
                op.status = OpStatus.WAITING
                self._try_reserve(op)
            else:
                op.status = OpStatus.READY
            if op.type is OpType.ADJUSTMENT:
                op.needs_approval = self._adjustment_needs_approval(op)
            return op

    def check_availability(self, op_id: int) -> Operation:
        """Retry reserving stock for a WAITING operation."""
        with self._lock:
            op = self._op(op_id)
            if op.status is not OpStatus.WAITING:
                raise InvalidOperation(f"{op.ref} is {op.status.value}, not waiting")
            self._try_reserve(op)
            return op

    def approve(self, op_id: int, user: str) -> Operation:
        """Manager approves a large adjustment. Creator can't approve their own."""
        with self._lock:
            op = self._op(op_id)
            if op.type is not OpType.ADJUSTMENT:
                raise InvalidOperation("Only adjustments need approval")
            if op.status not in OPEN_STATUSES:
                raise InvalidOperation(f"{op.ref} is {op.status.value}")
            if user == op.created_by:
                raise InvalidOperation("You can't approve your own adjustment")
            op.approved_by = user
            return op

    def validate(self, op_id: int, user: str = "system") -> Operation:
        """Apply the operation to stock. All-or-nothing: if any line fails, nothing changes."""
        with self._lock:
            op = self._op(op_id)
            if op.status is OpStatus.DRAFT:
                self.confirm(op_id)
            if op.status is OpStatus.WAITING:
                self._try_reserve(op)
                if op.status is OpStatus.WAITING:
                    raise InsufficientStock(f"{op.ref}: not enough stock at the source location")
            if op.status is not OpStatus.READY:
                raise InvalidOperation(f"{op.ref} is {op.status.value} and can't be validated")

            if op.type is OpType.ADJUSTMENT:
                op.needs_approval = self._adjustment_needs_approval(op)
                if op.needs_approval and not op.approved_by:
                    raise ApprovalRequired(
                        f"{op.ref} changes stock by more than {self.approval_threshold} "
                        f"units and needs a manager's approval"
                    )

            moves = self._moves_for(op)
            self._check_moves(moves)
            if op.type in RESERVING_TYPES:
                self._release(op)
            self._apply_moves(op, moves, user)
            self._mark_done(op, user)
            return op

    def cancel(self, op_id: int, user: str = "system") -> Operation:
        with self._lock:
            op = self._op(op_id)
            if op.status is OpStatus.DONE:
                raise InvalidOperation(f"{op.ref} is done; use reverse() instead")
            if op.status is OpStatus.CANCELED:
                raise InvalidOperation(f"{op.ref} is already canceled")
            if op.status is OpStatus.READY and op.type in RESERVING_TYPES:
                self._release(op)
            op.status = OpStatus.CANCELED
            op.note = (op.note + f" | canceled by {user}").strip(" |")
            return op

    def reverse(self, op_id: int, user: str = "system", note: str = "") -> Operation:
        """Undo a DONE operation by creating a new operation with the opposite moves.
        Nothing is deleted, so the ledger keeps a full history."""
        with self._lock:
            op = self._op(op_id)
            if op.status is not OpStatus.DONE:
                raise InvalidOperation(f"Only done operations can be reversed ({op.ref} is {op.status.value})")
            if op.reverses_id is not None:
                raise InvalidOperation(f"{op.ref} is itself a reversal")
            if op.reversed_by_id is not None:
                raise InvalidOperation(f"{op.ref} was already reversed")

            entries = [e for e in self.store.ledger if e.operation_id == op.id]
            moves: list[Move] = [(e.product_id, e.to_location_id, e.from_location_id, e.qty)
                                 for e in entries]
            self._check_moves(moves)

            if op.type is OpType.ADJUSTMENT:
                src, dst = None, op.dst_location_id
            else:
                src, dst = op.dst_location_id, op.src_location_id
            rev = self._new_operation(
                op.type, [OperationLine(e.product_id, e.qty) for e in entries],
                src=src, dst=dst, partner=op.partner, reason=op.reason, user=user,
                note=note or f"Reversal of {op.ref}",
            )
            rev.reverses_id = op.id
            self._apply_moves(rev, moves, user)
            self._mark_done(rev, user)
            op.reversed_by_id = rev.id
            return rev

    # ------------------------------------------------------------------ queries
    def quant_at(self, product_id: int, location_id: int) -> Quant:
        self._product(product_id)
        self._location(location_id)
        return self.store.quant(product_id, location_id)

    def total_on_hand(self, product_id: int) -> Decimal:
        return self._total(product_id, "on_hand")

    def stock_of(self, product_id: int) -> dict:
        """Stock availability per location for one product."""
        self._product(product_id)
        rows = []
        for (pid, lid), q in self.store.quants.items():
            if pid != product_id:
                continue
            loc = self.store.locations[lid]
            rows.append({
                "location_id": lid, "location": loc.name, "warehouse": loc.warehouse,
                "on_hand": q.on_hand, "reserved": q.reserved, "available": q.available,
            })
        return {
            "product_id": product_id,
            "on_hand": sum((r["on_hand"] for r in rows), ZERO),
            "reserved": sum((r["reserved"] for r in rows), ZERO),
            "available": sum((r["available"] for r in rows), ZERO),
            "by_location": rows,
        }

    def avg_daily_usage(self, product_id: int, days: int = 30) -> Decimal:
        """Average units delivered per day over the last `days` days (net of reversals)."""
        since = now() - timedelta(days=days)
        net = ZERO
        for e in self.store.ledger:
            if (e.product_id != product_id or e.operation_type is not OpType.DELIVERY
                    or e.timestamp < since):
                continue
            if e.to_location_id is None:
                net += e.qty
            elif e.from_location_id is None:
                net -= e.qty
        return max(net, ZERO) / Decimal(days)

    def low_stock(self) -> list[dict]:
        """Products at/below their reorder point or out of stock, with a suggested order qty."""
        result = []
        for p in self.store.products.values():
            available = self._total(p.id, "available")
            if available > 0 and available > p.min_qty:
                continue
            incoming = self._incoming(p.id)
            projected = available + incoming
            suggested = max(p.reorder_qty, p.min_qty - projected) if projected <= p.min_qty else ZERO
            usage = self.avg_daily_usage(p.id)
            result.append({
                "product_id": p.id, "sku": p.sku, "name": p.name,
                "status": "out_of_stock" if available <= 0 else "low_stock",
                "available": available, "min_qty": p.min_qty, "incoming": incoming,
                "suggested_order_qty": suggested,
                "days_of_cover": round(available / usage, 1) if usage > 0 else None,
            })
        return result

    def create_reorder_receipts(self, location_id: int, user: str = "system") -> Optional[Operation]:
        """Auto-draft ONE receipt for everything that needs reordering. Returns None if nothing needed."""
        with self._lock:
            lines = [(x["product_id"], x["suggested_order_qty"])
                     for x in self.low_stock() if x["suggested_order_qty"] > 0]
            if not lines:
                return None
            return self.create_receipt(location_id, lines, partner="Auto-reorder",
                                       user=user, note="Created from reorder rules")

    def list_operations(self, op_type=None, status=None, warehouse: Optional[str] = None,
                        category: Optional[str] = None) -> list[Operation]:
        """Dashboard filters: document type, status, warehouse, product category."""
        ops = list(self.store.operations.values())
        if op_type:
            t = OpType(op_type)
            ops = [o for o in ops if o.type is t]
        if status:
            s = OpStatus(status)
            ops = [o for o in ops if o.status is s]
        if warehouse:
            ops = [o for o in ops if any(
                self.store.locations[lid].warehouse == warehouse
                for lid in (o.src_location_id, o.dst_location_id) if lid is not None)]
        if category:
            ops = [o for o in ops if any(
                self.store.products[l.product_id].category == category for l in o.lines)]
        return sorted(ops, key=lambda o: o.created_at, reverse=True)

    def move_history(self, product_id: Optional[int] = None, location_id: Optional[int] = None,
                     op_type=None, user: Optional[str] = None,
                     since=None, until=None) -> list[LedgerEntry]:
        entries = self.store.ledger
        if product_id is not None:
            entries = [e for e in entries if e.product_id == product_id]
        if location_id is not None:
            entries = [e for e in entries
                       if location_id in (e.from_location_id, e.to_location_id)]
        if op_type:
            t = OpType(op_type)
            entries = [e for e in entries if e.operation_type is t]
        if user:
            entries = [e for e in entries if e.user == user]
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        if until:
            entries = [e for e in entries if e.timestamp <= until]
        return sorted(entries, key=lambda e: e.id, reverse=True)

    def dashboard_kpis(self) -> dict:
        low = self.low_stock()
        open_ops = [o for o in self.store.operations.values() if o.status in OPEN_STATUSES]
        products = self.store.products
        return {
            "total_products_in_stock": sum(1 for p in products.values() if self.total_on_hand(p.id) > 0),
            "low_stock_items": sum(1 for x in low if x["status"] == "low_stock"),
            "out_of_stock_items": sum(1 for x in low if x["status"] == "out_of_stock"),
            "pending_receipts": sum(1 for o in open_ops if o.type is OpType.RECEIPT),
            "pending_deliveries": sum(1 for o in open_ops if o.type is OpType.DELIVERY),
            "internal_transfers_scheduled": sum(1 for o in open_ops if o.type is OpType.INTERNAL),
            "adjustments_awaiting_approval": sum(
                1 for o in open_ops
                if o.type is OpType.ADJUSTMENT and o.needs_approval and not o.approved_by),
            "inventory_value": sum(
                (q.on_hand * products[pid].unit_cost for (pid, _), q in self.store.quants.items()),
                ZERO),
        }

    # ------------------------------------------------------------------ internals
    def _create(self, op_type: OpType, lines: LineInput, src=None, dst=None, partner=None,
                reason=None, user="system", note="") -> Operation:
        with self._lock:
            parsed: list[OperationLine] = []
            seen: set[int] = set()
            for product_id, qty in lines:
                if not self._product(product_id).active:
                    raise InvalidOperation(f"Product {product_id} is archived")
                q = to_qty(qty)
                if op_type is OpType.ADJUSTMENT:
                    if q < 0:
                        raise InvalidOperation("Counted quantity can't be negative")
                    if product_id in seen:
                        raise InvalidOperation("Each product can appear only once in an adjustment")
                    seen.add(product_id)
                elif q <= 0:
                    raise InvalidOperation("Quantity must be greater than zero")
                parsed.append(OperationLine(product_id, q))
            if not parsed:
                raise InvalidOperation("An operation needs at least one line")
            for lid in (src, dst):
                if lid is not None:
                    self._location(lid)
            return self._new_operation(op_type, parsed, src=src, dst=dst, partner=partner,
                                       reason=reason, user=user, note=note)

    def _new_operation(self, op_type, lines, src, dst, partner, reason, user, note) -> Operation:
        seq = self.store.next_id(f"ref:{op_type.value}")
        op = Operation(
            id=self.store.next_id("operation"),
            ref=f"WH/{REF_PREFIX[op_type]}/{seq:04d}",
            type=op_type, lines=lines, src_location_id=src, dst_location_id=dst,
            partner=partner, reason=reason, note=note, created_by=user,
        )
        self.store.operations[op.id] = op
        return op

    def _totals(self, op: Operation) -> dict[int, Decimal]:
        totals: dict[int, Decimal] = defaultdict(lambda: ZERO)
        for line in op.lines:
            totals[line.product_id] += line.qty
        return totals

    def _try_reserve(self, op: Operation) -> None:
        """All-or-nothing reservation at the source location."""
        needed = self._totals(op)
        src = op.src_location_id
        if all(self.store.quant(pid, src).available >= q for pid, q in needed.items()):
            for pid, q in needed.items():
                self.store.quant(pid, src).reserved += q
            op.status = OpStatus.READY

    def _release(self, op: Operation) -> None:
        for pid, q in self._totals(op).items():
            quant = self.store.quant(pid, op.src_location_id)
            quant.reserved = max(ZERO, quant.reserved - q)

    def _adjustment_needs_approval(self, op: Operation) -> bool:
        if self.approval_threshold is None:
            return False
        loc = op.dst_location_id
        return any(abs(l.qty - self.store.quant(l.product_id, loc).on_hand) > self.approval_threshold
                   for l in op.lines)

    def _moves_for(self, op: Operation) -> list[Move]:
        if op.type is OpType.RECEIPT:
            return [(l.product_id, None, op.dst_location_id, l.qty) for l in op.lines]
        if op.type is OpType.DELIVERY:
            return [(l.product_id, op.src_location_id, None, l.qty) for l in op.lines]
        if op.type is OpType.INTERNAL:
            return [(l.product_id, op.src_location_id, op.dst_location_id, l.qty) for l in op.lines]
        # ADJUSTMENT: move only the difference between counted and recorded
        moves: list[Move] = []
        loc = op.dst_location_id
        for l in op.lines:
            diff = l.qty - self.store.quant(l.product_id, loc).on_hand
            if diff > 0:
                moves.append((l.product_id, None, loc, diff))
            elif diff < 0:
                moves.append((l.product_id, loc, None, -diff))
        return moves

    def _check_moves(self, moves: list[Move]) -> None:
        """Make sure no location would go below zero. Checks everything before changing anything."""
        outflow: dict[tuple[int, int], Decimal] = defaultdict(lambda: ZERO)
        for pid, src, _dst, qty in moves:
            if src is not None:
                outflow[(pid, src)] += qty
        for (pid, lid), qty in outflow.items():
            on_hand = self.store.quant(pid, lid).on_hand
            if on_hand < qty:
                p, loc = self.store.products[pid], self.store.locations[lid]
                raise InsufficientStock(
                    f"Only {on_hand} {p.uom} of {p.name} at {loc.name}, need {qty}")

    def _apply_moves(self, op: Operation, moves: list[Move], user: str) -> None:
        for pid, src, dst, qty in moves:
            if src is not None:
                self.store.quant(pid, src).on_hand -= qty
            if dst is not None:
                self.store.quant(pid, dst).on_hand += qty
            self.store.ledger.append(LedgerEntry(
                id=self.store.next_id("ledger"), timestamp=now(), product_id=pid, qty=qty,
                from_location_id=src, to_location_id=dst, operation_id=op.id,
                operation_ref=op.ref, operation_type=op.type, user=user,
            ))

    def _mark_done(self, op: Operation, user: str) -> None:
        op.status = OpStatus.DONE
        op.validated_by = user
        op.validated_at = now()

    def _total(self, product_id: int, attr: str) -> Decimal:
        return sum((getattr(q, attr) for (pid, _), q in self.store.quants.items()
                    if pid == product_id), ZERO)

    def _incoming(self, product_id: int) -> Decimal:
        return sum((l.qty for o in self.store.operations.values()
                    if o.type is OpType.RECEIPT and o.status in OPEN_STATUSES
                    for l in o.lines if l.product_id == product_id), ZERO)

    def _stock_status(self, p: Product, available: Decimal) -> str:
        if available <= 0:
            return "out_of_stock"
        if available <= p.min_qty:
            return "low_stock"
        return "in_stock"

    def _has_history(self, product_id: int) -> bool:
        return any(e.product_id == product_id for e in self.store.ledger)

    def _has_open_operations(self, product_id: int) -> bool:
        return any(o.status in OPEN_STATUSES and any(l.product_id == product_id for l in o.lines)
                   for o in self.store.operations.values())

    def _product(self, product_id: int) -> Product:
        try:
            return self.store.products[product_id]
        except KeyError:
            raise NotFound(f"Product {product_id} not found")

    def _location(self, location_id: int) -> Location:
        try:
            return self.store.locations[location_id]
        except KeyError:
            raise NotFound(f"Location {location_id} not found")

    def _op(self, op_id: int) -> Operation:
        try:
            return self.store.operations[op_id]
        except KeyError:
            raise NotFound(f"Operation {op_id} not found")

