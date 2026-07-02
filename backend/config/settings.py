from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Stock Market Researcher API"
    openai_api_key: str = os.getenv("OPENAI_API_KEY","")
    newsapi_key: str = os.getenv("NEWSAPI_KEY","")
    base_url:str = os.getenv("OPENAI_BASE_URL","")
    database_url: str = os.getenv("DATABASE_URL","")
    redis_url: str = os.getenv("REDIS_URL","")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
