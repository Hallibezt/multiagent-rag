# Multi-Agent RAG — Engineering Bible

> The constitution for this repo. Every session, every agent reads this file first. No exceptions.
>
> **This project has TWO deliverables of equal weight:**
> 1. A working, **deployed, observable** multi-agent RAG service.
> 2. **Halli's deep understanding of it** — traceable through code, infra, and theory.
>
> Code that ships without a matching `/learning` doc is **unfinished**. See Rule 0.

## Session Start

1. **Read this file** — the rules below must never be violated.
2. **Read `docs/plans/product-roadmap.md`** — find the first unchecked item. That's what we're working on.
3. **`git log --oneline -20`** — see what was done recently.
4. **Before writing any non-trivial LangGraph / pgvector / LangChain code**, ground it against the *current* official docs (Rule 1). These APIs change and are the #1 hallucination risk.

---

## What we're building (one screen)

A **supervisor / orchestrator-worker** multi-agent RAG service:

- **Supervisor agent** — classifies the incoming question and *routes* it. Does no work itself.
- **RAG agent** — semantic retrieval over unstructured documents (pgvector).
- **SQL agent** — text-to-SQL over structured tables.
- A **shared, typed state object** flows through the graph (see Rule 5).
- A real backend around it: FastAPI, Postgres-checkpointed state, observability, containerised, deployed to Kubernetes with network-scoped agent reach.

**The point of this project is *operating* an agent system in production — not agent cleverness.** See Rule 2.

**Data source: GuestPad (decided 2026-07-13).** See "GuestPad Data Map" below.

---

## Prime Directives

### Rule 0 — Learning-first (SUPREME RULE for this project)

> Halli is a DevOps engineer building depth in LLM/RAG systems. The gap between what the AI understands and what Halli understands must **not** be allowed to grow. Closing it is a first-class deliverable, not a nicety.

- **Every implementation step ships with a plain-English doc in `/learning/`.** A feature/infra change is not "done" until its learning doc exists. See `/learning/README.md` for the format.
- Explain **like the reader is a sharp engineer who is new to *this specific* technology** — define every acronym, show the actual files/commands, link the theory, name the gotchas, and tell the reader how to trace it themselves.
- When Claude writes code, Claude also writes (or updates) the learning doc **in the same turn**. This is enforced, not optional.
- Prefer clarity Halli can re-derive later over cleverness only the AI can maintain.

### Rule 1 — No hallucinated solutions (NON-NEGOTIABLE)

> Code that compiles is not code that works. A plausible API name is not a real API name.

- **"I don't know" is a required answer** when uncertain. Never fabricate API names, library functions, package names, config keys, SQL/vector operators, or Kubernetes fields.
- Label non-trivial technical claims **FACT** (verified) / **INFERENCE** (derived) / **SPECULATION** (guess).
- **LangGraph / LangChain / pgvector change frequently.** For any non-trivial call: state the version targeted, and ground against the *current* official docs (paste them in or fetch them live) **before** writing graph-construction, checkpointing, state-schema, or vector-query code.
- **Packages:** state exact name + source; every dependency is verified on PyPI before install.
- **Kubernetes:** every generated manifest is flagged as needing `kubectl apply --dry-run=server` before it is applied.
- **pgvector / SQL:** do not assume a vector function, operator, or index type exists — confirm against the installed pgvector version.
- When unsure of a current API or version, **STOP and verify** (docs / web) rather than guess. This is cheaper than debugging a hallucination.

### Rule 2 — Operational layer first

- **Three nodes done properly beats seven nodes on a laptop.** Do **not** add a fourth/fifth agent, fancy routing, or agent cleverness for its own sake.
- Invest disproportionately in: **recovery** (checkpoint/resume), **observability** (tracing from day one), **scoping** (NetworkPolicy), **deployment** (containers, health checks, k8s).
- If a suggestion trades operational robustness for agent sophistication, it is the wrong suggestion.

### Rule 3 — Scope discipline & phases

- Build in phases (see "Definition of Done"). Each phase has a concrete "done"; earlier phases must work before later ones start. **Do not expand scope mid-phase.**
- **Non-goals** (out of scope unless Halli says otherwise): a polished frontend/UI; more than three agents; multi-tenant concerns; fine-tuning any model; supporting more than one data domain *at runtime* (but keep the seams — Rule 4).

### Rule 4 — The three seams (cheap multi-version readiness)

Build **GuestPad concretely first**. Do **not** pay for multi-domain up front (premature abstraction). But keep three nearly-free seams open so "add Aurora later" is a config + ingestion job, not a refactor:

1. **Don't hardcode the corpus/DB source inside graph nodes** — inject it from config.
2. **Keep the typed state domain-neutral** — the envelope owns `retrieval` / `sql` / `answer`; it never mentions "hot tub" or "aurora".
3. **Treat `(which corpus, which schema, which scope)` as deployment config** from day one — even with only one value today.

Multi-version lives in the **config / deployment / network-scoping layer**, one domain per deploy. That is on-thesis (Rule 2), not scope creep (Rule 3).

### Rule 5 — State-schema discipline

- Model shared state as **nested, typed structures with clear per-agent ownership** (`state.retrieval`, `state.sql`, `state.answer`) — **not** one flat dict.
- The state schema **ages worst** once checkpoints are persisted. Get it right early; changing it after Phase 2 means migrating live checkpoints.

---

## Architecture (current best thinking — not dogma)

| Concern | Choice | Note |
|---|---|---|
| Orchestration | **LangGraph** | Nodes = agents/functions; edges = transitions incl. conditional routing. Model-agnostic. |
| Vector store | **pgvector inside Postgres** | No separate vector DB. GuestPad is greenfield on pgvector — we build this. |
| Service layer | **FastAPI** | HTTP API in front of the graph. |
| Graph state | **Postgres checkpointing** | Explicitly **not** in-memory — a run must recover after a crash. |
| Observability | **Langfuse or LangSmith** | Wired from the first working version. |
| Model access | **Model-agnostic, default Claude** (Anthropic API) | Keep the provider swappable (resilience + regulated-setting point). |
| Deployment | **Kubernetes (Rancher / RKE2)** | Health checks + a **NetworkPolicy** scoping agent reach (SQL agent must not reach the doc store, and vice versa). |

---

## Stack & Version Policy

**Language:** Python (target 3.12+ — confirm at setup).
**Libraries (names only — versions are pinned & verified at install, never asserted from memory):** LangGraph + its Postgres checkpointer, FastAPI, an async Postgres driver, the pgvector client/extension, Pydantic, the Anthropic SDK, and a tracing SDK (Langfuse/LangSmith).

> **Version policy (Rule 1):** every dependency's exact version is resolved against PyPI / official docs at the moment we add it, pinned in the dependency file, and recorded in the relevant `/learning` doc with the doc URL used to ground it. No version numbers are written into this repo from memory.

---

## GuestPad Data Map (the two surfaces)

**RAG corpus** (embed at record granularity, property-scoped; content is bilingual en/is):
`how_to_guides.content` · `amenities.guide_text` · `house_rules.text` · `local_guides.description` + `owner_note` · `poi_inventory.description` (159 real Icelandic POIs) · `eat_drink_places.description` · `tours.description` · `announcements.content` · `properties.welcome_message` / `emergency_info`.

**SQL surface** (scope to ~12–15 operational tables — **not** all 61):
`properties` · `tablets` · `bookings` · `table_bookings` · `room_service_orders` (+items) · `shop_orders` (+items) · `menu_items` (+categories) · `restaurant_tables` · `restaurant_operating_hours` · `tours` · `payments`.

> Full analysis + example routing questions live in the memory note `multiagent-rag-data-source` and will be lifted into `docs/` when we `/design`.

---

## Definition of Done (phased)

- **Phase 0 — Ingestion.** pgvector table stood up; a real GuestPad corpus chunked + embedded. *Done when:* a similarity query returns sensible chunks.
- **Phase 1 — The graph.** Supervisor + RAG + SQL agents, shared typed state, running locally against the real schema. *Done when:* the example routing questions return correct answers via the correct agent(s).
- **Phase 2 — Service / MLOps.** FastAPI wrapper; Postgres checkpointing; tracing wired in. *Done when:* a run interrupted mid-flight resumes from its checkpoint, and every run is traceable.
- **Phase 3 — Operations.** Containerise; deploy to Kubernetes; health checks; a NetworkPolicy scoping agent reach. *Done when:* it runs on the cluster, healthy, and the SQL agent provably cannot reach the document store.

---

## Conventions

- **Commits:** conventional style (`feat:`, `fix:`, `chore:`, `docs:`…). **Do NOT add a `Co-Authored-By` trailer or any "Generated with Claude" line** — Halli's explicit preference for this repo.
- **Branching:** work off `main`; commit/push only when Halli asks.
- **Secrets:** never commit. `.env` is gitignored; `.env.example` documents every required key.
- **Docs stay in sync:** when a phase item completes, check it off in `docs/plans/product-roadmap.md` before moving on. Never close a session with unmarked completed work.
- **Learning docs:** every code/infra change → a matching `/learning` doc, same turn (Rule 0).

---

## Working Mode

Halli + Claude, with **Claude as the hardworker** — move fast, keep momentum. But speed never overrides:
- the **learning doc** (Rule 0),
- the **verification steps** (Rule 1 — verify packages, ground APIs, dry-run manifests),
- the **operational-first** priority (Rule 2).

When a build step involves a LangGraph/pgvector API Claude doesn't already know cold, the fast path *is* grounding it against current docs first — not guessing and debugging later.
