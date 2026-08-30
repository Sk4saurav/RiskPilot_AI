import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# For SaaS platform production, this will be PostgreSQL. Fallback to SQLite for local generation.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./riskpilot.db")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session
