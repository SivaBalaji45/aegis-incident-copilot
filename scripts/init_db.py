"""Create all tables against DATABASE_URL_ASYNC. MVP schema management —
swap for Alembic migrations once the schema needs to evolve without a wipe.

Usage: python scripts/init_db.py
"""

import asyncio

from sqlalchemy import text

from aegis.db.models import Base
from aegis.db.session import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print("Schema created.")


if __name__ == "__main__":
    asyncio.run(main())
