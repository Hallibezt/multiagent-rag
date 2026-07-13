# 00 — Orientation: what this project actually is

> Read this first. It explains the whole system in plain English before we write a line of
> graph code. No prior LangGraph/RAG knowledge assumed. Every acronym is defined the first
> time it appears.

## The one-sentence version

We're building a service where a person asks a question in plain language, and a small team
of specialised AI "agents" figures out **who should answer it** — the one that reads
documents, or the one that queries the database — and returns a grounded answer.

## The words, defined

- **LLM (Large Language Model)** — the AI that reads and writes text (e.g. Claude). It's
  smart but has no memory of *your* data and will confidently make things up if you let it.
- **RAG (Retrieval-Augmented Generation)** — the fix for "making things up." Instead of
  asking the LLM to answer from memory, you first **retrieve** the relevant facts from
  *your* data and hand them to the LLM to answer *from*. "Augmenting" the model's
  generation with retrieved context. Grounded answers, fewer hallucinations.
- **Embedding** — a way to turn a piece of text into a list of numbers (a "vector") that
  captures its *meaning*. Two texts about the same idea end up with similar number-lists,
  even if they use different words. This is what makes "semantic" (meaning-based) search
  possible.
- **Vector search / similarity search** — given the embedding of your question, find the
  stored text chunks whose embeddings are closest (most similar in meaning). That's how the
  RAG agent finds the right paragraph without keyword matching.
- **pgvector** — a Postgres extension that lets the database *store* those number-lists and
  *do* the "find the closest ones" search directly in SQL. So we don't need a separate
  vector database — our existing Postgres does it.
- **Agent** — an LLM given a specific job and a specific set of tools. Here we have three,
  each narrow on purpose.
- **Supervisor / orchestrator-worker pattern** — one agent (the supervisor) doesn't answer
  anything itself; it just *decides which worker* should handle the question and routes it
  there. Workers do the actual work. Classic, boring-in-a-good-way design.
- **LangGraph** — the framework that wires these agents together as a **graph**: each agent
  is a *node*, and the arrows between them (*edges*) decide what runs next. It also
  remembers the state of a run so it can survive a crash (see checkpointing).
- **State** — one shared, structured object that travels through the graph. Each agent reads
  from it and writes its results back into its own section (`state.retrieval`, `state.sql`,
  `state.answer`). Think of it as the case file passed desk to desk.
- **Checkpointing** — saving that state object to a database (Postgres) after each step, so
  if the process dies mid-run, it can **resume from where it stopped** instead of starting
  over. This is the difference between a demo and something production-worthy.
- **FastAPI** — the Python web framework that puts an HTTP door in front of the graph, so
  other programs (or a curl command) can send it a question.
- **Kubernetes (k8s)** — the system that runs our containerised service on a cluster,
  restarts it if it's unhealthy, and (via a **NetworkPolicy**) can *fence off* what each
  part is allowed to talk to.

## Why three agents and not one big one

Because our data has two genuinely different shapes, and the *right way to answer* differs:

- **Unstructured documents** (a house-rules paragraph, a "how to use the hot tub" guide) →
  best answered by **semantic retrieval** (the RAG agent).
- **Structured records** (bookings, menu prices, opening hours) → best answered by
  **turning the question into a SQL query** (the SQL agent).

A question like *"What are the sauna rules, and is the kitchen open for room service right
now?"* needs **both**: retrieve the sauna-rules text **and** query the live opening hours.
The **supervisor** is what notices that and fans the work out. That split is the whole
reason a multi-agent design is justified here (and not over-engineering).

## The data flow (what happens to one question)

```
  Person: "What are the sauna rules, and is the kitchen open right now?"
        │
        ▼
  FastAPI  ──────────────────────────────  (HTTP door)
        │
        ▼
  LangGraph run  ── creates a State object ──┐
        │                                    │  ← checkpointed to Postgres
        ▼                                    │     after every step, so a
  Supervisor node  (classify + route)        │     crash can resume
        ├──────────────► RAG agent node      │
        │                 embed the question │
        │                 → pgvector finds    │
        │                   the sauna-rules   │
        │                   chunk → drafts    │
        │                   that half         │
        └──────────────► SQL agent node       │
                          question → SQL      │
                          → runs on Postgres  │
                          → opening-hours row │
                          → drafts that half  │
        ┌───────────────────────────────────┘
        ▼
  Answer assembled in State  ──►  FastAPI response  ──►  Person
        │
        └── every step traced in Langfuse/LangSmith (we can see exactly what happened)
```

## The stack, and why each piece is here

| Piece | Job | Why this one |
|-------|-----|-------------|
| **LangGraph** | wire the agents into a graph, hold state, checkpoint it | most-adopted multi-agent framework; model-agnostic; persistence is the production feature |
| **pgvector in Postgres** | store embeddings + do similarity search | reuse one database instead of standing up a separate vector DB |
| **FastAPI** | HTTP API in front of the graph | standard, async, Python-native |
| **Postgres checkpointing** | resume a run after a crash | this is what makes it *not* a laptop demo |
| **Langfuse / LangSmith** | trace every step | you can't operate what you can't see |
| **Claude (Anthropic API)** | the LLM doing the reasoning | default provider; kept swappable on purpose |
| **Kubernetes + NetworkPolicy** | run it, keep it healthy, fence the agents | the *operating it in production* story — the point of the project |

## Where the data comes from

**GuestPad** — a tablet-based guest-concierge product. It gives us both shapes in one
Postgres database: real concierge **documents** (house rules, how-to guides, local guides,
159 Icelandic points-of-interest) *and* real operational **tables** (bookings, menus,
opening hours, payments). See the "GuestPad Data Map" in `../CLAUDE.md`.

## The mental model to hold onto

> The clever-sounding part (the agents) is the *easy* part — a three-node graph is a
> weekend. The part that makes this real, and the part worth the effort, is everything
> **around** it: it recovers from a crash, you can *see* every run, it's deployed on a
> cluster, and each agent is fenced to only the data it needs. That's Rule 2 in `../CLAUDE.md`,
> and it's why this project is a portfolio piece and not a tutorial.

## Next

When we start **Phase 0 (ingestion)**, the next doc — `01-…` — will explain, at this same
level of detail, how we turn GuestPad's document columns into embedded, searchable chunks in
pgvector, with the real commands and the real gotchas.
