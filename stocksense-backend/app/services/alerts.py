import threading
from datetime import datetime, timezone
from typing import Optional

from app.engine import OpStatus, OpType, StockEngine

OPEN = (OpStatus.DRAFT, OpStatus.WAITING, OpStatus.READY)


class AlertItem:
    def __init__(self, id: int, kind: str, message: str,
                 product_id: Optional[int] = None, operation_id: Optional[int] = None):
        self.id = id
        self.kind = kind                      # low_stock | out_of_stock | approval_needed
        self.message = message
        self.product_id = product_id
        self.operation_id = operation_id
        self.created_at = datetime.now(timezone.utc)
        self.read = False
        self.resolved_at: Optional[datetime] = None


class AlertCenter:
    def __init__(self):
        self.alerts: dict[int, AlertItem] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def refresh(self, eng: StockEngine) -> list[AlertItem]:
        """Sync alerts with the engine. Returns only newly created alerts."""
        with self._lock:
            return self._refresh(eng)

    def _refresh(self, eng: StockEngine) -> list[AlertItem]:
        now = datetime.now(timezone.utc)
        new_alerts: list[AlertItem] = []

        # ---- current problems ----
        low_items = eng.low_stock()
        low_pids = {item["product_id"]: item["status"] for item in low_items}
        pending_ops = {
            op.id: op for op in eng.store.operations.values()
            if op.type is OpType.ADJUSTMENT and op.needs_approval
            and not op.approved_by and op.status in OPEN
        }

        # ---- auto-resolve alerts whose problem is gone ----
        for a in self.alerts.values():
            if a.resolved_at is not None:
                continue
            if a.kind in ("low_stock", "out_of_stock"):
                if low_pids.get(a.product_id) != a.kind:
                    a.resolved_at = now
            elif a.kind == "approval_needed":
                if a.operation_id not in pending_ops:
                    a.resolved_at = now

        # ---- create alerts for new problems ----
        for item in low_items:
            pid, kind = item["product_id"], item["status"]
            if not self._has_active(kind, product_id=pid):
                p = eng.get_product(pid)
                if kind == "out_of_stock":
                    msg = f"{p.name} ({p.sku}) is out of stock"
                else:
                    msg = f"{p.name} ({p.sku}) is low: {item['available']} {p.uom} left (min {p.min_qty})"
                if item["suggested_order_qty"] > 0:
                    msg += f". Suggested order: {item['suggested_order_qty']} {p.uom}"
                new_alerts.append(self._add_alert(kind, msg, product_id=pid))

        for op in pending_ops.values():
            if not self._has_active("approval_needed", operation_id=op.id):
                msg = f"Adjustment {op.ref} needs manager approval (created by {op.created_by})"
                new_alerts.append(self._add_alert("approval_needed", msg, operation_id=op.id))

        return new_alerts

    def _has_active(self, kind: str, product_id: Optional[int] = None,
                    operation_id: Optional[int] = None) -> bool:
        return any(
            a.kind == kind and a.resolved_at is None
            and (product_id is None or a.product_id == product_id)
            and (operation_id is None or a.operation_id == operation_id)
            for a in self.alerts.values()
        )

    def _add_alert(self, kind: str, message: str, product_id: Optional[int] = None,
                   operation_id: Optional[int] = None) -> AlertItem:
        aid = self._next_id
        self._next_id += 1
        item = AlertItem(aid, kind, message, product_id, operation_id)
        self.alerts[aid] = item
        return item

    def list_alerts(self, unread_only: bool = False, include_resolved: bool = False) -> list[AlertItem]:
        items = list(self.alerts.values())
        if not include_resolved:
            items = [i for i in items if i.resolved_at is None]
        if unread_only:
            items = [i for i in items if not i.read]
        return sorted(items, key=lambda i: i.id, reverse=True)

    def mark_read(self, alert_id: int) -> Optional[AlertItem]:
        item = self.alerts.get(alert_id)
        if item:
            item.read = True
        return item

    def mark_all_read(self) -> int:
        count = 0
        for item in self.alerts.values():
            if not item.read and item.resolved_at is None:
                item.read = True
                count += 1
        return count