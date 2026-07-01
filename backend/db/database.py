from __future__ import annotations

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config.settings import get_settings

settings = get_settings()

_raw_url = settings.database_url or "sqlite:///./stock_market_researcher.db"

# Build driver-prefixed URL and connect_args for the async engine
_connect_args: dict = {}
if _raw_url.startswith("sqlite"):
    _db_url = _raw_url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif _raw_url.startswith("postgresql://") or _raw_url.startswith("postgres://"):
    # Strip query params that asyncpg doesn't understand (channel_binding, sslmode)
    # and pass ssl=True via connect_args instead
    parsed = urlparse(_raw_url)
    _db_url = urlunparse(parsed._replace(
        scheme="postgresql+asyncpg",
        query=""  # remove ?sslmode=require&channel_binding=require
    ))
    _connect_args = {"ssl": True}
else:
    _db_url = _raw_url  # already has driver prefix

engine = create_async_engine(_db_url, echo=False, connect_args=_connect_args)

AsyncSessionLocal=async_sessionmaker(engine,expire_on_commit=False)


class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    """Create all tables on startup (async-safe via run_sync)."""
    async with engine.begin() as conn:
        from db import models  # noqa: F401 — registers ORM models with Base
        await conn.run_sync(Base.metadata.create_all)