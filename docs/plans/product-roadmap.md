# Product Roadmap — Multi-Agent RAG

> Lightweight phase tracker (Session Start reads this). Check items off `[x]` as they land.
> This will be expanded into proper work plans via `/plan` when we start each phase.
> Full rationale lives in `../../CLAUDE.md` and the `multiagent-rag-data-source` memory note.

**Decided:** data source = **GuestPad**. Three-agent supervisor pattern. Three cheap
multi-version seams baked in (CLAUDE.md Rule 4).

---

## Phase 0 — Ingestion ✅ COMPLETE
*Done when: a similarity query returns sensible chunks from real GuestPad content.* ✓ verified

- [x] Decide Python project tooling + pin verified versions (Rule 1) — uv + Python 3.13; versions verified vs PyPI + locked in `uv.lock`; two-store docker-compose + injected config; smoke test
- [x] Access to a GuestPad Postgres — connected read-only; extracted 247 docs → `data/seed/documents.jsonl` (extract → seed → ingest, so it also runs with **zero** GuestPad access)
- [x] Stand up the pgvector table(s) — `documents` table, `vector(384)`, HNSW cosine index
- [x] Chunk + embed the GuestPad document columns — 252 chunks, local fastembed (keyless)
- [x] Similarity query returns sensible chunks  ← **Phase 0 gate PASSED** (hot tub, waterfalls, checkout, beach-safety all resolve correctly)
- [x] `/learning/01-*` + `/learning/02-*` written

## Phase 1 — The graph (core)  ✅ COMPLETE
*Done when: the example routing questions return correct answers via the correct agent(s).* ✓ verified (rag / sql / both)

- [x] Define the shared typed state (Rule 5: nested, per-agent ownership) — `graph/state.py`
- [x] RAG agent node (pgvector retrieval) — wraps Phase 0 search
- [x] Supervisor node — **LLM classifier** via `messages.parse` (validated route enum), grounded against claude-api; models config-injected (default `claude-opus-4-8`, router swappable to `claude-haiku-4-5`)
- [x] SQL agent node — synthetic transactional seed + **safe read-only text-to-SQL** (SELECT-validated + `conn.read_only`); verified exact (13 confirmed bookings / 637k ISK)
- [x] Fan-out to BOTH agents (parallel superstep) + `synthesize` merge node — workers gather, synthesizer composes (Rule 5 keeps parallel writes collision-free)
- [x] Example routing questions pass  ← **Phase 1 gate PASSED** (rag / sql / both all correct)
- [x] Learning docs: `/learning/03`–`/learning/06` written

## Phase 2 — Service / MLOps layer  ✅ COMPLETE
*Done when: an interrupted run resumes from its checkpoint, and every run is traceable.* ✓ both verified

- [x] Postgres checkpointing (NOT in-memory) — dedicated `checkpoint-store` + `PostgresSaver`; grounded against the installed 3.1.0 API
- [x] Kill a run mid-flight → it resumes from checkpoint — **proven** (`make checkpoint-demo`: pause → checkpoint → fresh process restores state → resume, workers not re-run)
- [x] FastAPI wrapper around the graph — `/ask` + `/health`, pooled checkpointer, request carries a `thread_id`; verified
- [x] Tracing wired in — **self-hosted Langfuse** (vendored 6-service stack, headless-init keys, opt-in callback); verified a run's trace landed via the Langfuse API  ← **Phase 2 gate PASSED**
- [x] Learning docs: `/learning/07`–`/learning/09` written

## Phase 3 — Operations
*Done when: it runs on the cluster, healthy, and the SQL agent provably cannot reach the doc store.*

- [ ] Containerise + health checks
- [ ] Deploy to **minikube** with an enforcing CNI (Calico/Cilium — default minikube does NOT enforce NetworkPolicy) — `--dry-run=server` every manifest first (Rule 1)
- [ ] NetworkPolicy scoping agent reach (stand doc store + SQL DB up as *separate* endpoints so it's enforceable — Rule 4 seam)
- [ ] Prove SQL agent cannot reach the document store  ← **Phase 3 gate**
- [ ] *Stretch:* redeploy the same manifests to GKE or AKS (managed-cloud demo) — verify current pricing first (Rule 1), use an ephemeral cluster + teardown
- [ ] Learning docs written

---

## Non-goals (Rule 3)
Polished UI · more than three agents · multi-tenant concerns · fine-tuning · more than one
data domain *at runtime* (seams kept for a later config-only Aurora instance).
