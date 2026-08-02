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

# Monkeypatch litellm.completion to map reasoning_content to content for reasoning models
_original_litellm_completion = litellm.completion
def _patched_litellm_completion(*args, **kwargs):
    resp = _original_litellm_completion(*args, **kwargs)
    try:
        for choice in getattr(resp, "choices", []):
            msg = getattr(choice, "message", None)
            if msg and getattr(msg, "content", None) is None:
                reasoning = getattr(msg, "reasoning_content", None)
                if reasoning:
                    msg.content = reasoning
    except Exception:
        pass
    return resp
litellm.completion = _patched_litellm_completion


from crewai import LLM
from config.settings import get_settings
settings = get_settings()

_PROVIDER_CONFIGS: dict[str, dict] = {
    "gemini": {
        "model": "gemini/gemini-2.5-flash",
        "api_key_attr": "gemini_api_key",
        "temperature": 0.7,
    },
    "mistral": {
        "model": "mistral/ministral-3b-2512",
        "api_key_attr": "mistral_api_key",
        "temperature": 0,
    },
    # DeepSeek hosted via NVIDIA NIM — uses nvidia_nim/ prefix so LiteLLM
    # sends the full namespaced model ID (deepseek-ai/deepseek-v4-flash) to NIM.
    "deepseek": {
        "model": "nvidia_nim/deepseek-ai/deepseek-v4-flash",
        "api_key_attr": "nvidia_nim_key",
        "temperature": 0,
    },
    # GPT-OSS-20B hosted via NVIDIA NIM — nvidia_nim/ preserves openai/gpt-oss-20b
    # intact; using openai/ prefix causes LiteLLM to strip it → 404.
    "openai": {
        "model": "nvidia_nim/openai/gpt-oss-20b",
        "api_key_attr": "nvidia_nim_key",
        "temperature": 0,
    },
}


def load_configurable_llm(provider: str | None = None) -> LLM:
    p = (provider or settings.llm_provider).lower().strip()
    cfg = _PROVIDER_CONFIGS.get(p, _PROVIDER_CONFIGS["openai"])

    kwargs: dict = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
    }

    # Resolve API key
    api_key_attr = cfg.get("api_key_attr")
    if api_key_attr:
        kwargs["api_key"] = getattr(settings, api_key_attr, None) or os.getenv(api_key_attr.upper(), "")

    # Resolve optional api_base
    if "api_base" in cfg:
        kwargs["api_base"] = cfg["api_base"]
    elif "api_base_attr" in cfg:
        base = getattr(settings, cfg["api_base_attr"], None) or os.getenv("OPENAI_BASE_URL", "")
        if base:
            kwargs["api_base"] = base

    return LLM(**kwargs)


# Module-level singleton using the env-configured default
llm = load_configurable_llm()


def get_llm(provider: str | None = None) -> LLM:
    """Return a per-provider LLM instance.

    Returns the cached module-level singleton when `provider` is None or
    matches the env-configured default; otherwise builds a fresh instance.
    """
    if not provider or provider.lower().strip() == settings.llm_provider.lower().strip():
        return llm
    return load_configurable_llm(provider)
