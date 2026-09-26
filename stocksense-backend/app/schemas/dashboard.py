from .common import OutModel, Qty


class KpisOut(OutModel):
    total_products_in_stock: int
    low_stock_items: int
    out_of_stock_items: int
    pending_receipts: int
    pending_deliveries: int
    internal_transfers_scheduled: int
    adjustments_awaiting_approval: int
    inventory_value: Qty
