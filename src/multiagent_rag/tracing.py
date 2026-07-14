"""Observability: attach a Langfuse callback to graph runs (Phase 2).

Tracing is OPT-IN — it turns on only when the Langfuse keys are set (see
`.env.example`). Without them, `callbacks()` returns `[]` and the app runs
untraced (so `make ask` stays fast with nothing running). Langfuse is
self-hosted (`make langfuse-up`); the callback traces every graph run — the
route decision and each node (supervisor, rag, sql, synthesize).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from multiagent_rag.config import settings


@lru_cache(maxsize=1)
def _handler() -> Any | None:
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler

    # Initialize the global client explicitly from settings (not os.environ), then
    # the callback handler picks it up.
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return CallbackHandler()


def callbacks() -> list:
    """For LangGraph's `config["callbacks"]` — `[handler]` if tracing is on, else `[]`."""
    handler = _handler()
    return [handler] if handler is not None else []


def flush() -> None:
    """Send any buffered traces — call at the end of a short-lived (CLI) run."""
    if _handler() is not None:
        from langfuse import get_client

        get_client().flush()
