from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Stock Market Researcher API"
    openai_api_key: str = ""
    newsapi_key: str = ""
    database_url: str = "sqlite:///./stock_market_researcher.db"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
