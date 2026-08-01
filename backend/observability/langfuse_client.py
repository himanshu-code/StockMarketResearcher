from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Generator

from langfuse import get_client
import contextvars
import langfuse
import types

# Monkeypatch Langfuse.__init__ to ignore sdk_integration parameter from LiteLLM
if not hasattr(langfuse.Langfuse, "_original_langfuse_init"):
    _original_langfuse_init = langfuse.Langfuse.__init__
    def _patched_langfuse_init(self, *args, **kwargs):
        kwargs.pop("sdk_integration", None)
        _original_langfuse_init(self, *args, **kwargs)
    langfuse.Langfuse.__init__ = _patched_langfuse_init
    langfuse.Langfuse._original_langfuse_init = _original_langfuse_init

# Monkeypatch langfuse.version to prevent LiteLLM AttributeError
if not hasattr(langfuse, "version"):
    langfuse_version_module = types.ModuleType("langfuse.version")
    langfuse_version_module.__version__ = langfuse.__version__
    langfuse.version = langfuse_version_module
    sys_modules = __import__("sys").modules
    sys_modules["langfuse.version"] = langfuse_version_module

# Monkeypatch Langfuse to support legacy v2 trace() calls (needed by LiteLLM)
import hashlib
import uuid
import datetime

def _to_valid_trace_id(tid):
    if not tid:
        return uuid.uuid4().hex
    clean = str(tid).replace("-", "").lower()
    if len(clean) == 32:
        try:
            int(clean, 16)
            return clean
        except ValueError:
            pass
    return hashlib.md5(str(tid).encode("utf-8")).hexdigest()

def _to_nanoseconds(dt):
    if isinstance(dt, datetime.datetime):
        return int(dt.timestamp() * 1e9)
    if isinstance(dt, (int, float)):
        return int(dt * 1e9)
    return None

_VALID_OBSERVATION_KEYS = {
    "trace_context", "name", "as_type", "input", "output", "metadata",
    "version", "level", "status_message", "completion_start_time", "model",
    "model_parameters", "usage_details", "cost_details", "prompt"
}

class LegacyTraceWrapper:
    def __init__(self, client, trace_id, name=None, **kwargs):
        self.client = client
        self.trace_id = _to_valid_trace_id(trace_id)
        self.name = name

    def generation(self, **kwargs):
        params = {k: v for k, v in kwargs.items() if k in _VALID_OBSERVATION_KEYS}
        params["trace_context"] = {"trace_id": self.trace_id}
        params["as_type"] = "generation"
        obs = self.client.start_observation(**params)
        end_time_val = _to_nanoseconds(kwargs.get("end_time"))
        if hasattr(obs, "end"):
            try:
                obs.end(end_time=end_time_val)
            except Exception:
                obs.end()
        return obs

    def span(self, **kwargs):
        params = {k: v for k, v in kwargs.items() if k in _VALID_OBSERVATION_KEYS}
        params["trace_context"] = {"trace_id": self.trace_id}
        params["as_type"] = "span"
        obs = self.client.start_observation(**params)
        end_time_val = _to_nanoseconds(kwargs.get("end_time"))
        if hasattr(obs, "end"):
            try:
                obs.end(end_time=end_time_val)
            except Exception:
                obs.end()
        return obs

    def event(self, **kwargs):
        _VALID_EVENT_KEYS = {"trace_context", "name", "input", "output", "metadata", "version", "level", "status_message"}
        params = {k: v for k, v in kwargs.items() if k in _VALID_EVENT_KEYS}
        params["trace_context"] = {"trace_id": self.trace_id}
        return self.client.create_event(**params)

    def update(self, **kwargs):
        pass

def _langfuse_trace(self, *args, **kwargs):
    trace_id = None
    name = None
    if args:
        first_arg = args[0]
        if hasattr(first_arg, "id"):
            trace_id = getattr(first_arg, "id")
        if hasattr(first_arg, "name"):
            name = getattr(first_arg, "name")
    if not trace_id:
        trace_id = kwargs.get("id") or kwargs.get("trace_id")
    if not name:
        name = kwargs.get("name")
    return LegacyTraceWrapper(self, trace_id, name)

if not hasattr(langfuse.Langfuse, "trace"):
    langfuse.Langfuse.trace = _langfuse_trace


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
