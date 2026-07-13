# /learning — the "explain it so I actually understand it" folder

This folder exists because of **Rule 0** in `../CLAUDE.md`: this project is as much about
*Halli understanding the system* as it is about shipping it. Every meaningful piece of
code or infra gets a doc here that explains it from the ground up.

## Who these docs are for

**Me (Halli) — six months from now, in an interview, or debugging at 2am.** A sharp
engineer who is *new to this specific technology* (LangGraph, pgvector, RAG internals).
Not a beginner at software — a beginner at *this*. So: define the jargon, show the real
files, and never hand-wave the part that's actually hard.

## The rule (enforced, not optional)

> When Claude writes or changes code/infra, Claude writes or updates the matching learning
> doc **in the same turn**. Code without a learning doc is unfinished.

## The format for each doc

Every numbered doc follows the same shape so they're skimmable and trustworthy:

1. **What it is** — in plain English, one paragraph, no jargon (or jargon defined inline).
2. **Why we chose it** — the decision and the alternatives we rejected.
3. **How it works here** — the *actual* files, functions, commands, and config in this repo.
4. **The theory** — the concept underneath, with links to the grounding docs (and the
   version those docs describe — see Rule 1).
5. **Gotchas** — what bit us, or what would bite a newcomer.
6. **Trace it yourself** — exact files to open / commands to run to see it working.

Anything the author isn't certain is current is marked **[VERIFY]** with a link, per Rule 1.

## Index

| Doc | Topic | Status |
|-----|-------|--------|
| [00-orientation.md](00-orientation.md) | The whole project in plain English: RAG, agents, the stack, the data flow | ✅ |
| _01-…_ | _(added as we build Phase 0: pgvector ingestion)_ | ⏳ |

_The index grows as we build. One row per doc._
