import os
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
    else:
        return LLM(
            model='openai/gpt-4o-mini',
            api_base=settings.base_url or os.getenv("OPENAI_BASE_URL"),
            api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0
        )
llm = load_configurable_llm()