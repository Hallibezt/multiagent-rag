"""The sql-store schema — the single source of truth for the SQL agent.

Used twice: to CREATE the tables (seed.py), and to tell the LLM exactly what it
may query (query.py). A small, realistic slice of an accommodation's operational
data — enough that everyday questions force a real SQL query.
"""

SCHEMA_DDL = """
CREATE TABLE bookings (
    id           serial PRIMARY KEY,
    guest_name   text NOT NULL,
    tour_name    text NOT NULL,
    booking_date date NOT NULL,
    party_size   int  NOT NULL,
    amount_isk   int  NOT NULL,
    status       text NOT NULL          -- confirmed | pending | cancelled
);

CREATE TABLE menu_items (
    id        serial PRIMARY KEY,
    name      text NOT NULL,
    category  text NOT NULL,            -- starter | main | dessert | drink
    price_isk int  NOT NULL,
    is_vegan  boolean NOT NULL
);

CREATE TABLE table_bookings (
    id           serial PRIMARY KEY,
    guest_name   text NOT NULL,
    booking_date date NOT NULL,
    start_time   time NOT NULL,
    party_size   int  NOT NULL,
    status       text NOT NULL          -- confirmed | pending | cancelled
);

CREATE TABLE room_service_orders (
    id         serial PRIMARY KEY,
    item       text NOT NULL,
    quantity   int  NOT NULL,
    total_isk  int  NOT NULL,
    ordered_at timestamp NOT NULL,
    status     text NOT NULL            -- delivered | preparing | cancelled
);
"""

TABLES = ["bookings", "menu_items", "table_bookings", "room_service_orders"]
