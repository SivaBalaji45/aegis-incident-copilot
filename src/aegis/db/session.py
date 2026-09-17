"""Async SQLAlchemy engine/session wiring. Import `get_session` as a FastAPI
dependency or `session_scope()` as a plain async context manager elsewhere
(e.g. the scheduler, which runs outside request scope)."""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from aegis.config import settings

engine = create_async_engine(settings.database_url_async, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
