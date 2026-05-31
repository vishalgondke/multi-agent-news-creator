"""Async SQLAlchemy engine / session setup.

Supports two backends (selected by settings.db_backend):
  * sqlite  -> zero-setup local file, tables auto-created (default)
  * mysql   -> Docker MySQL, schema from app/db/init.sql
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_is_sqlite = settings.db_backend == "sqlite"

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=not _is_sqlite,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create tables if they don't exist (used for the SQLite backend)."""
    # ensure models are imported so metadata is populated
    from app.models import db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency."""
    async with SessionLocal() as session:
        yield session
