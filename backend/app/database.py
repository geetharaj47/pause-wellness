from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.config import settings

# SQLite connection arguments adjustment
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Allow multiple threads to access SQLite async connections safely
    connect_args["check_same_thread"] = False

# Create the async SQL engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

# Async session maker
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db() -> None:
    """Initializes database tables asynchronously."""
    async with engine.begin() as conn:
        # Create tables from SQLModel metadata registry
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding async sessions for FastAPI handlers."""
    async with async_session_maker() as session:
        yield session
