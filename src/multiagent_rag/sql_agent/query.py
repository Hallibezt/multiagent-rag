"""Text-to-SQL over the sql-store — the SQL agent's evidence-gathering half.

Claude turns a question + the schema into ONE SELECT; we validate it's read-only,
run it in a read-only session (defense in depth — an LLM could emit DROP/DELETE),
and return the query + rows. Turning rows into prose is the graph's `synthesize`
node — this module only gathers.
"""

from __future__ import annotations

import re

import psycopg
from pydantic import BaseModel

from multiagent_rag import llm
from multiagent_rag.config import settings
from multiagent_rag.sql_agent.schema import SCHEMA_DDL


class _SQL(BaseModel):
    sql: str


_GEN_SYSTEM = f"""You write ONE read-only PostgreSQL SELECT that answers the guest's question.

You may query ONLY these tables:
{SCHEMA_DDL}

Rules:
- SELECT only. Never INSERT/UPDATE/DELETE or any DDL, and no semicolons.
- Use CURRENT_DATE for relative dates like "today", "this weekend", "upcoming".
- Always include a LIMIT of at most 100.
Return only the query."""

_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b", re.I)


def _validate(sql: str) -> str:
    """First line of defense: reject anything that isn't a single SELECT/CTE."""
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        raise ValueError("multiple statements are not allowed")
    if not s.lower().startswith(("select", "with")):
        raise ValueError(f"only SELECT queries are allowed, got: {s[:40]!r}")
    if _FORBIDDEN.search(s):
        raise ValueError("query contains a forbidden keyword")
    return s


def run_query(question: str) -> tuple[str, list[dict]]:
    """Generate a SELECT for the question, validate it, run it read-only, return
    (sql, rows)."""
    generated = llm.structured(_GEN_SYSTEM, question, _SQL, model=settings.llm_model, max_tokens=400)
    sql = _validate(generated.sql)

    with psycopg.connect(settings.sql_store_dsn) as conn:
        conn.read_only = True  # enforced by Postgres — any write raises
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchmany(100)]
    return sql, rows
