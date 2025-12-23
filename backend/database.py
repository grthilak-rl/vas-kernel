"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.settings import settings


# Database engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


