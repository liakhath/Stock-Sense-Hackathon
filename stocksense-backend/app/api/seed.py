"""Demo data so the frontend has something to show while there's no database."""
from app.engine import StockEngine


def seed_demo(eng: StockEngine) -> None:
    main = eng.add_location("Stock", "Main Warehouse")
    eng.add_location("Rack A", "Main Warehouse")
    floor = eng.add_location("Production Floor", "Main Warehouse")
    wh2 = eng.add_location("Stock", "Warehouse 2")

    steel = eng.add_product("Steel Rod", "STL-001", "Raw Material", "kg",
                            min_qty=50, reorder_qty=200, unit_cost=65)
    chair = eng.add_product("Office Chair", "CHR-001", "Furniture", "unit",
                            min_qty=10, reorder_qty=40, unit_cost=2500)
    desk = eng.add_product("Standing Desk", "DSK-001", "Furniture", "unit",
                           min_qty=5, reorder_qty=20, unit_cost=6000)
    bolt = eng.add_product("Hex Bolt M8", "BLT-M8", "Hardware", "box",
                           min_qty=20, reorder_qty=100, unit_cost=120)
    paint = eng.add_product("Primer Paint", "PNT-001", "Consumables", "litre",
                            min_qty=15, reorder_qty=50, unit_cost=300)

    r = eng.create_receipt(main.id, [(steel.id, 100), (chair.id, 30), (desk.id, 4), (bolt.id, 150)],
                           partner="Tata Steel", user="manager")
    eng.validate(r.id, user="manager")

    t = eng.create_transfer(main.id, floor.id, [(steel.id, 60)], user="staff")
    eng.validate(t.id, user="staff")

    d = eng.create_delivery(main.id, [(chair.id, 10)], partner="Acme Corp", user="staff")
    eng.validate(d.id, user="staff")

    eng.create_delivery(main.id, [(desk.id, 2)], partner="Globex", user="staff")        # pending
    eng.create_receipt(wh2.id, [(paint.id, 40)], partner="Asian Paints", user="manager")  # pending

    a = eng.create_adjustment(main.id, [(bolt.id, 145)], reason="damaged", user="staff")
    eng.validate(a.id, user="staff")