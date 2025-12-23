"""Initialize database tables."""
import asyncio
from database import engine, Base
from app.models import device, stream, recording, bookmark, snapshot


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())

