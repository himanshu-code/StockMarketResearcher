from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Generator

from langfuse import get_client
import contextvars


logger = logging.getLogger(__name__)

_active_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "langfuse_trace_id", default=None
)


def set_active_trace_id(trace_id: str) -> None:
    _active_trace_id.set(trace_id)


def get_active_trace_id() -> str | None:
    return _active_trace_id.get()


@lru_cache(maxsize=1)
def get_langfuse_client():
    client = get_client()
    if not client.auth_check():
        logger.warning("[Langfuse] Auth check failed")
    return client


@dataclass
class TraceHandle:
    """Thin wrapper returned by make_trace so callers can access trace.id, update(), and flush()."""
    id: str
    observation: Any

    def update(self, *args, **kwargs):
        # Safely convert 'metadat' typo to 'metadata'
        if "metadat" in kwargs:
            kwargs["metadata"] = kwargs.pop("metadat")
        self.observation.update(*args, **kwargs)

    def flush(self):
        # Flush the client
        get_langfuse_client().flush()


def make_trace(
    name: str,
    *,
    ticker: str,
    job_id: str,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TraceHandle:
    """
    Create a root Langfuse trace (v3/v4 SDK) and return a TraceHandle with .id.

    In SDK v3+, traces are created via start_as_current_observation().
    We start the root span, grab the trace ID, then detach — the span stays
    open for the lifetime of the process (fire-and-forget root context).
    The actual workflow observations are nested inside by the agents.
    """
    lf = get_langfuse_client()

    # Use the job_id as a deterministic trace seed so the trace ID is stable
    # even if this function is accidentally called twice for the same job.
    trace_id = lf.create_trace_id(seed=job_id)

    # Start the root observation (this becomes the trace root in Langfuse).
    # We use start_observation because it returns a handle and does not require
    # a `with` statement context manager to execute.
    obs = lf.start_observation(
        as_type="span",
        name=name,
        trace_context={"trace_id": trace_id},
        input={"ticker": ticker, "job_id": job_id},
        metadata=metadata or {},
    )

    # Propagate trace ID into the context var so downstream code can read it.
    set_active_trace_id(trace_id)

    return TraceHandle(id=trace_id, observation=obs)
