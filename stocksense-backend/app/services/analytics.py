"""Reports: fast/slow movers, dead stock, inventory valuation, CSV exports."""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from app.engine import StockEngine
from app.engine.models import LedgerEntry, OpType, now

ZERO = Decimal("0")


def _flows(eng: StockEngine, days: int):
    """Net qty shipped (deliveries) and received (receipts) per product in the window.
    Reversals are subtracted."""
    since = now() - timedelta(days=days)
    shipped, received = defaultdict(lambda: ZERO), defaultdict(lambda: ZERO)
    for e in eng.store.ledger:
        if e.timestamp < since:
            continue
        if e.operation_type is OpType.DELIVERY:
            if e.to_location_id is None:
                shipped[e.product_id] += e.qty
            elif e.from_location_id is None:
                shipped[e.product_id] -= e.qty
        elif e.operation_type is OpType.RECEIPT:
            if e.from_location_id is None:
                received[e.product_id] += e.qty
            elif e.to_location_id is None:
                received[e.product_id] -= e.qty
    return shipped, received


def movers(eng: StockEngine, days: int = 30, top: int = 5) -> dict:
    shipped, received = _flows(eng, days)
    rows = []
    for p in eng.store.products.values():
        if not p.active:
            continue
        on_hand = eng.total_on_hand(p.id)
        out = max(shipped[p.id], ZERO)
        daily = out / Decimal(days)
        rows.append({
            "product_id": p.id, "sku": p.sku, "name": p.name, "category": p.category,
            "on_hand": on_hand, "shipped": out, "received": max(received[p.id], ZERO),
            "avg_daily": round(daily, 2),
            "days_of_cover": round(on_hand / daily, 1) if daily > 0 else None,
            "stock_value": on_hand * p.unit_cost,
        })
    moving = [r for r in rows if r["shipped"] > 0]
    return {
        "days": days,
        "fast_movers": sorted(moving, key=lambda r: r["shipped"], reverse=True)[:top],
        "slow_movers": sorted([r for r in moving if r["on_hand"] > 0],
                              key=lambda r: r["shipped"])[:top],
        # has stock but nothing shipped in the window -> money stuck on shelves
        "dead_stock": sorted([r for r in rows if r["shipped"] == 0 and r["on_hand"] > 0],
                             key=lambda r: r["stock_value"], reverse=True),
    }


def valuation(eng: StockEngine) -> dict:
    by_cat, by_wh = defaultdict(lambda: ZERO), defaultdict(lambda: ZERO)
    for (pid, lid), q in eng.store.quants.items():
        if q.on_hand == 0:
            continue
        p = eng.store.products[pid]
        value = q.on_hand * p.unit_cost
        by_cat[p.category] += value
        by_wh[eng.store.locations[lid].warehouse] += value

    def as_rows(d):
        return [{"name": k, "value": v} for k, v in sorted(d.items(), key=lambda kv: kv[1], reverse=True)]

    return {"total": sum(by_cat.values(), ZERO),
            "by_category": as_rows(by_cat), "by_warehouse": as_rows(by_wh)}


def stock_csv(eng: StockEngine) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["sku", "product", "category", "uom", "warehouse", "location",
                "on_hand", "reserved", "available", "unit_cost", "stock_value"])
    rows = []
    for (pid, lid), q in eng.store.quants.items():
        if q.on_hand == 0 and q.reserved == 0:
            continue
        p, l = eng.store.products[pid], eng.store.locations[lid]
        rows.append([p.sku, p.name, p.category, p.uom, l.warehouse, l.name,
                     q.on_hand, q.reserved, q.available, p.unit_cost, q.on_hand * p.unit_cost])
    for r in sorted(rows, key=lambda r: (r[0], r[4], r[5])):
        w.writerow(r)
    return buf.getvalue()


def _loc_label(eng: StockEngine, loc_id, op_type: OpType) -> str:
    if loc_id is not None:
        l = eng.store.locations[loc_id]
        return f"{l.warehouse} / {l.name}"
    return {OpType.RECEIPT: "Vendor", OpType.DELIVERY: "Customer",
            OpType.ADJUSTMENT: "Inventory adjustment"}.get(op_type, "-")


def ledger_csv(eng: StockEngine, entries: list[LedgerEntry]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "reference", "type", "sku", "product", "qty", "from", "to", "user"])
    for e in entries:
        p = eng.store.products[e.product_id]
        w.writerow([e.timestamp.isoformat(timespec="seconds"), e.operation_ref,
                    e.operation_type.value, p.sku, p.name, e.qty,
                    _loc_label(eng, e.from_location_id, e.operation_type),
                    _loc_label(eng, e.to_location_id, e.operation_type), e.user])
    return buf.getvalue()