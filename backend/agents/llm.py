import os
import litellm

# Enable dropping extra parameters not supported by the destination model
litellm.drop_params = True

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