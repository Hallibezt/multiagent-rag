"""Thin wrapper around the Anthropic SDK — the model-agnostic seam.

Grounded against the claude-api reference (July 2026): the default model is
`claude-opus-4-8`; on 4.8 we must NOT send `temperature`/`top_p`/`budget_tokens`
(they return 400). Classification uses `messages.parse()` with a Pydantic schema
for validated, low-latency structured output.

Keeping every LLM call behind this module means swapping providers later is a
one-file change (CLAUDE.md: model-agnostic by design).
"""

from __future__ import annotations

from typing import TypeVar

import anthropic
from pydantic import BaseModel

from multiagent_rag.config import settings

T = TypeVar("T", bound=BaseModel)

_client: anthropic.Anthropic | None = None


def _get() -> anthropic.Anthropic:
    """Lazily construct the client so importing this module needs no API key."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def text(system: str, user: str, *, model: str | None = None, max_tokens: int = 1024) -> str:
    """A plain text completion. Returns the concatenated text blocks."""
    resp = _get().messages.create(
        model=model or settings.llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def structured(system: str, user: str, schema: type[T], *, model: str | None = None, max_tokens: int = 128) -> T:
    """A validated structured response — `messages.parse` constrains output to
    `schema` and returns the parsed Pydantic instance."""
    resp = _get().messages.parse(
        model=model or settings.llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
    )
    return resp.parsed_output
