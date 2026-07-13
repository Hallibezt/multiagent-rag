"""Postgres helpers.

`connect()` opens a psycopg 3 connection and registers pgvector's type adapters,
so a Python list (or numpy array) maps to the Postgres `vector` type and back
automatically — no manual serialisation.
"""

from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

from multiagent_rag.config import settings


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Open a connection with pgvector adapters registered.

    Defaults to the document store. The caller owns the connection — use it as a
    context manager so it commits and closes cleanly:

        with connect() as conn, conn.cursor() as cur:
            cur.execute(...)
    """
    conn = psycopg.connect(dsn or settings.doc_store_dsn)
    register_vector(conn)
    return conn
