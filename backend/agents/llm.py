import os
import litellm

# Monkeypatch langfuse.version to prevent LiteLLM AttributeError
import langfuse
import sys
import types
if not hasattr(langfuse, "version"):
    langfuse_version_module = types.ModuleType("langfuse.version")
    langfuse_version_module.__version__ = langfuse.__version__
    langfuse.version = langfuse_version_module
    sys.modules["langfuse.version"] = langfuse_version_module

# Monkeypatch Langfuse.__init__ to ignore sdk_integration parameter from LiteLLM
_original_langfuse_init = langfuse.Langfuse.__init__
def _patched_langfuse_init(self, *args, **kwargs):
    kwargs.pop("sdk_integration", None)
    _original_langfuse_init(self, *args, **kwargs)
langfuse.Langfuse.__init__ = _patched_langfuse_init

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

# Enable dropping extra parameters not supported by the destination model
litellm.drop_params = True
litellm.success_callback=["langfuse"]
litellm.failure_callback=["langfuse"]

# Monkeypatch CrewAI's Anthropic prompt caching marker to do nothing.
# This prevents it from injecting the "cache_breakpoint: true" parameter into
# messages when calling non-Anthropic providers like Mistral, which reject it.
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except ImportError:
    pass

from crewai import LLM
from config.settings import get_settings
settings = get_settings()
def load_configurable_llm() -> LLM:
    provider = settings.llm_provider.lower().strip()
    if provider == "gemini":
        return LLM(
            model="gemini/gemini-2.5-flash",
            api_key=settings.gemini_api_key or os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
    elif provider == "mistral":
        return LLM(
            model="mistral/ministral-3b-2512",
            api_key=settings.mistral_api_key or os.getenv("MISTRAL_API_KEY"),
            temperature=0
        )
    else:
        return LLM(
            model='openai/gpt-4o-mini',
            api_base=settings.base_url or os.getenv("OPENAI_BASE_URL"),
            api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0
        )
llm = load_configurable_llm()