"""Seed SYNTHETIC transactional data into the sql-store (the SQL agent's surface).

GuestPad's real transactional tables are empty, so this generates plausible demo
rows — no real guest data, safe to commit publicly. Dates are relative to *today*
so "this weekend" / "upcoming" questions stay sensible whenever you run it.

Run:  make seed-sql   (or  uv run python -m multiagent_rag.sql_agent.seed)
"""

from __future__ import annotations

import datetime as dt

import psycopg

from multiagent_rag.config import settings
from multiagent_rag.sql_agent.schema import SCHEMA_DDL, TABLES


def _date(offset_days: int) -> dt.date:
    return dt.date.today() + dt.timedelta(days=offset_days)


def _ts(offset_days: int, hour: int) -> dt.datetime:
    return dt.datetime.combine(_date(offset_days), dt.time(hour, 0))


_GUESTS = [
    "Jón Þórsson", "Guðrún Sigurðardóttir", "Anna Bjarnadóttir", "Erik Larsson",
    "Mia Andersen", "Tom Fisher", "Sofia Rossi", "Lena Müller", "Kenji Tanaka",
]
_TOURS = [
    "Eyjafjallajökull Snowmobile Adventure", "Seljalandsfoss & Gljúfrabúi Walk",
    "South Coast Waterfalls", "Glacier Hike", "Northern Lights Hunt",
]

# (guest_idx, tour_idx, date_offset, party_size, amount_isk, status)
_BOOKINGS = [
    (0, 0, 1, 2, 58000, "confirmed"), (1, 1, 2, 4, 32000, "confirmed"),
    (2, 2, 2, 2, 24000, "pending"), (3, 4, 3, 6, 54000, "confirmed"),
    (4, 3, 5, 2, 46000, "confirmed"), (5, 0, 6, 3, 87000, "confirmed"),
    (6, 1, 7, 2, 16000, "cancelled"), (7, 2, 8, 4, 48000, "confirmed"),
    (8, 4, 9, 2, 18000, "pending"), (0, 3, 10, 2, 46000, "confirmed"),
    (1, 0, -2, 2, 58000, "confirmed"), (2, 1, -1, 5, 40000, "confirmed"),
    (3, 2, 0, 2, 24000, "confirmed"), (4, 4, 12, 8, 72000, "pending"),
    (5, 1, 3, 2, 16000, "confirmed"), (6, 3, 4, 4, 92000, "confirmed"),
    (7, 0, 11, 2, 58000, "cancelled"), (8, 2, 6, 3, 36000, "confirmed"),
]

# (name, category, price_isk, is_vegan)
_MENU = [
    ("Icelandic Lamb Soup", "starter", 2400, False),
    ("Roasted Beet & Walnut Salad", "starter", 2200, True),
    ("Pan-fried Arctic Char", "main", 5800, False),
    ("Slow-roasted Lamb Shoulder", "main", 6500, False),
    ("Wild Mushroom Risotto", "main", 4900, True),
    ("Grilled Vegetable Skewers", "main", 4200, True),
    ("Skyr with Berries", "dessert", 1900, False),
    ("Dark Chocolate Tart", "dessert", 2300, True),
    ("Vegan Rhubarb Crumble", "dessert", 2100, True),
    ("Craft Beer (Einstök)", "drink", 1600, True),
    ("House Red Wine", "drink", 1800, True),
    ("Hot Chocolate", "drink", 1200, False),
]

# (guest_idx, date_offset, hour, party_size, status)
_TABLE_BOOKINGS = [
    (0, 0, 19, 2, "confirmed"), (1, 0, 20, 4, "confirmed"), (2, 1, 19, 2, "pending"),
    (3, 1, 21, 6, "confirmed"), (4, 2, 20, 2, "confirmed"), (5, 2, 19, 3, "cancelled"),
    (6, 3, 20, 2, "confirmed"), (7, 4, 19, 4, "confirmed"), (8, 5, 20, 2, "pending"),
    (0, 6, 21, 5, "confirmed"),
]

# (item, quantity, total_isk, date_offset, hour, status)
_ROOM_SERVICE = [
    ("Hot Chocolate", 2, 2400, -1, 21, "delivered"), ("Craft Beer (Einstök)", 4, 6400, -1, 22, "delivered"),
    ("Skyr with Berries", 2, 3800, 0, 9, "delivered"), ("House Red Wine", 1, 1800, 0, 20, "preparing"),
    ("Icelandic Lamb Soup", 2, 4800, 0, 13, "delivered"), ("Dark Chocolate Tart", 3, 6900, 1, 21, "preparing"),
    ("Hot Chocolate", 1, 1200, 1, 8, "cancelled"), ("Wild Mushroom Risotto", 2, 9800, 2, 19, "delivered"),
    ("Craft Beer (Einstök)", 6, 9600, 2, 23, "delivered"), ("Vegan Rhubarb Crumble", 2, 4200, 3, 20, "preparing"),
]


def main() -> None:
    with psycopg.connect(settings.sql_store_dsn) as conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS " + ", ".join(TABLES) + " CASCADE")
        cur.execute(SCHEMA_DDL)

        cur.executemany(
            "INSERT INTO bookings (guest_name, tour_name, booking_date, party_size, amount_isk, status)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            [(_GUESTS[g], _TOURS[t], _date(o), p, a, s) for (g, t, o, p, a, s) in _BOOKINGS],
        )
        cur.executemany(
            "INSERT INTO menu_items (name, category, price_isk, is_vegan) VALUES (%s, %s, %s, %s)",
            _MENU,
        )
        cur.executemany(
            "INSERT INTO table_bookings (guest_name, booking_date, start_time, party_size, status)"
            " VALUES (%s, %s, %s, %s, %s)",
            [(_GUESTS[g], _date(o), dt.time(h, 0), p, s) for (g, o, h, p, s) in _TABLE_BOOKINGS],
        )
        cur.executemany(
            "INSERT INTO room_service_orders (item, quantity, total_isk, ordered_at, status)"
            " VALUES (%s, %s, %s, %s, %s)",
            [(i, q, tot, _ts(o, h), s) for (i, q, tot, o, h, s) in _ROOM_SERVICE],
        )

        counts = {}
        for t in TABLES:
            cur.execute(f"SELECT count(*) FROM {t}")
            counts[t] = cur.fetchone()[0]

    print("seeded synthetic transactional data into the sql-store:")
    for t, n in counts.items():
        print(f"  {t:<22} {n}")


if __name__ == "__main__":
    main()
