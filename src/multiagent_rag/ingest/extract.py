"""Extract GuestPad's document-shaped content into a portable seed file.

This is the ONE step that needs GuestPad access (read-only). It reads the
document-bearing columns, pulls the English text out of each bilingual
``{"en": ..., "is": ...}`` JSONB value, and writes ``data/seed/documents.jsonl``.
After this runs, ingestion works entirely from the seed — no GuestPad needed.

Run (needs a read-only GuestPad DSN in the environment):

    GUESTPAD_SOURCE_DSN=postgresql://... uv run python -m multiagent_rag.ingest.extract
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

import psycopg

# Per source table: which column is the human title, which column(s) hold the
# body text to embed, and which columns to keep as metadata.
SOURCES: dict[str, dict[str, object]] = {
    "how_to_guides": {"title": "title", "content": ["content"], "meta": ["icon"]},
    "amenities": {"title": "name", "content": ["guide_text"], "meta": ["icon"]},
    "house_rules": {"title": None, "content": ["text"], "meta": []},
    "local_guides": {
        "title": "name",
        "content": ["description", "owner_note"],
        "meta": ["category", "address"],
    },
    "poi_inventory": {
        "title": "name",
        "content": ["description"],
        "meta": ["category", "subcategory", "region"],
    },
    "eat_drink_places": {
        "title": "name",
        "content": ["description", "owner_note"],
        "meta": ["cuisine_type", "address"],
    },
    "tours": {
        "title": "title",
        "content": ["description"],
        "meta": ["category", "operator_name"],
    },
    "announcements": {"title": "title", "content": ["content"], "meta": ["type"]},
    "properties": {
        "title": "name",
        "content": ["welcome_message", "emergency_info", "house_rules"],
        "meta": ["slug"],
    },
}

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SEED_PATH = REPO_ROOT / "data" / "seed" / "documents.jsonl"


def en(value: object) -> str | None:
    """Pull the English text out of a bilingual value. Handles the shapes GuestPad
    actually uses: ``{"en": "..."}``, ``{"en": ["rule", "rule"]}``, plain strings,
    and bare lists. Returns None when there's nothing usable."""
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("en") or next((v for v in value.values() if v), None)
    if value is None:
        return None
    if isinstance(value, list):
        text = "\n".join(p for p in (en(v) for v in value) if p)
    else:
        text = str(value)
    text = text.strip()
    return text or None


def redact(text: str) -> str:
    """Mask obvious secrets so the seed is safe to commit publicly. GuestPad's
    demo data includes e.g. a WiFi password; credential-shaped strings should not
    live in a public repo."""
    return re.sub(r"(?i)(password[:\s]*)([^\s.,;]+)", r"\1<redacted>", text)


def columns_of(cur: psycopg.Cursor, table: str) -> set[str]:
    cur.execute(
        "select column_name from information_schema.columns "
        "where table_schema='public' and table_name=%s",
        (table,),
    )
    return {r[0] for r in cur.fetchall()}


def main() -> None:
    dsn = os.environ.get("GUESTPAD_SOURCE_DSN")
    if not dsn:
        sys.exit("Set GUESTPAD_SOURCE_DSN to a read-only GuestPad connection string.")

    SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []

    with psycopg.connect(dsn, connect_timeout=15) as conn, conn.cursor() as cur:
        for table, cfg in SOURCES.items():
            cols = columns_of(cur, table)
            wanted = ["id"]
            if "property_id" in cols:
                wanted.append("property_id")
            if cfg["title"] and cfg["title"] in cols:
                wanted.append(cfg["title"])
            wanted += [c for c in cfg["content"] if c in cols]
            wanted += [c for c in cfg["meta"] if c in cols]
            sel = ", ".join(f'"{c}"' for c in dict.fromkeys(wanted))
            cur.execute(f'select {sel} from public."{table}"')
            names = [d.name for d in cur.description]
            for row in cur.fetchall():
                r = dict(zip(names, row))
                content = "\n\n".join(
                    p for p in (en(r.get(c)) for c in cfg["content"]) if p
                )
                if not content:
                    continue
                content = redact(content)
                docs.append(
                    {
                        "source_table": table,
                        "source_id": str(r["id"]),
                        "property_id": str(r["property_id"])
                        if r.get("property_id")
                        else None,
                        "lang": "en",
                        "title": en(r.get(cfg["title"])) if cfg["title"] else None,
                        "content": content,
                        "metadata": {
                            c: r[c] for c in cfg["meta"] if r.get(c) is not None
                        },
                    }
                )

    with SEED_PATH.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    by_source: dict[str, int] = {}
    for d in docs:
        by_source[d["source_table"]] = by_source.get(d["source_table"], 0) + 1
    print(f"wrote {len(docs)} documents -> {SEED_PATH.relative_to(REPO_ROOT)}")
    for t, n in sorted(by_source.items()):
        print(f"  {t:<20} {n}")


if __name__ == "__main__":
    main()
