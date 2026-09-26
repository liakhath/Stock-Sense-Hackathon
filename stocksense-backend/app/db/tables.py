"""Database tables. They are created automatically on startup if they don't exist."""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, MetaData, Numeric, String, Table, Text,
)

metadata = MetaData()
QTY = Numeric(18, 4)

locations = Table(
    "locations", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("name", String(120), nullable=False),
    Column("warehouse", String(120), nullable=False),
)

products = Table(
    "products", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("name", String(200), nullable=False),
    Column("sku", String(100), nullable=False, unique=True),
    Column("category", String(120), nullable=False),
    Column("uom", String(30), nullable=False),
    Column("min_qty", QTY, nullable=False),
    Column("reorder_qty", QTY, nullable=False),
    Column("unit_cost", QTY, nullable=False),
    Column("active", Boolean, nullable=False),
)

stock_quants = Table(
    "stock_quants", metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("location_id", Integer, ForeignKey("locations.id"), primary_key=True),
    Column("on_hand", QTY, nullable=False),
    Column("reserved", QTY, nullable=False),
)

operations = Table(
    "operations", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("ref", String(40), nullable=False, unique=True),
    Column("type", String(20), nullable=False),
    Column("status", String(20), nullable=False),
    Column("src_location_id", Integer, ForeignKey("locations.id"), nullable=True),
    Column("dst_location_id", Integer, ForeignKey("locations.id"), nullable=True),
    Column("partner", String(200), nullable=True),
    Column("reason", String(30), nullable=True),
    Column("note", Text, nullable=False),
    Column("created_by", String(120), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("validated_by", String(120), nullable=True),
    Column("validated_at", DateTime(timezone=True), nullable=True),
    Column("needs_approval", Boolean, nullable=False),
    Column("approved_by", String(120), nullable=True),
    Column("reverses_id", Integer, nullable=True),
    Column("reversed_by_id", Integer, nullable=True),
)

operation_lines = Table(
    "operation_lines", metadata,
    Column("operation_id", Integer, ForeignKey("operations.id"), primary_key=True),
    Column("line_no", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("qty", QTY, nullable=False),
)

stock_ledger = Table(
    "stock_ledger", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("timestamp", DateTime(timezone=True), nullable=False, index=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False, index=True),
    Column("qty", QTY, nullable=False),
    Column("from_location_id", Integer, ForeignKey("locations.id"), nullable=True),
    Column("to_location_id", Integer, ForeignKey("locations.id"), nullable=True),
    Column("operation_id", Integer, ForeignKey("operations.id"), nullable=False),
    Column("operation_ref", String(40), nullable=False),
    Column("operation_type", String(20), nullable=False),
    Column("user_name", String(120), nullable=False),
)
