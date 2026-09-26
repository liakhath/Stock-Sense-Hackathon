from datetime import datetime, timezone
from typing import Optional

from app.engine import OpStatus, OpType, StockEngine


class AlertItem:
    def __init__(self, id: int, kind: str, message: str,
                 product_id: Optional[int] = None, operation_id: Optional[int] = None):
        self.id = id
        self.kind = kind
        self.message = message
        self.product_id = product_id
        self.operation_id = operation_id
        self.created_at = datetime.now(timezone.utc)
        self.read = False
        self.resolved_at = None


class AlertCenter:
    def __init__(self):
        self.alerts: dict[int, AlertItem] = {}
        self._next_id = 1

    def refresh(self, eng: StockEngine) -> list[AlertItem]:
        """Scan engine for low stock, out of stock, and pending approval operations. Returns newly created alerts."""
        new_alerts = []
        low_items = eng.low_stock()
        low_pids = {item["product_id"]: item["status"] for item in low_items}

        # Auto-resolve stock alerts if level returned to healthy
        for a in list(self.alerts.values()):
            if a.kind in ("low_stock", "out_of_stock") and a.product_id and a.resolved_at is None:
                if a.product_id not in low_pids or low_pids[a.product_id] != a.kind:
                    a.resolved_at = datetime.now(timezone.utc)

        for item in low_items:
            pid = item["product_id"]
            kind = item["status"]  # "low_stock" or "out_of_stock"
            if not any(a.kind == kind and a.product_id == pid and a.resolved_at is None for a in self.alerts.values()):
                msg = f"{item['name']} ({item['sku']}) is {kind.replace('_', ' ')}: {item['available']} available (min {item['min_qty']})"
                new_alerts.append(self._add_alert(kind, msg, product_id=pid))

        for op in eng.store.operations.values():
            if op.type is OpType.ADJUSTMENT and op.needs_approval and not op.approved_by and op.status in (OpStatus.DRAFT, OpStatus.WAITING, OpStatus.READY):
                if not any(a.kind == "approval_needed" and a.operation_id == op.id and a.resolved_at is None for a in self.alerts.values()):
                    msg = f"Adjustment {op.ref} needs manager approval"
                    new_alerts.append(self._add_alert("approval_needed", msg, operation_id=op.id))

        return new_alerts




    def _add_alert(self, kind: str, message: str, product_id: Optional[int] = None, operation_id: Optional[int] = None) -> AlertItem:
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
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def mark_read(self, alert_id: int) -> Optional[AlertItem]:
        item = self.alerts.get(alert_id)
        if item:
            item.read = True
        return item

    def mark_all_read(self) -> int:
        count = 0
        for item in self.alerts.values():
            if not item.read:
                item.read = True
                count += 1
        return count
