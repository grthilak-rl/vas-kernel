"""
Manually create snapshots table.
"""
import asyncio
from database import engine, Base
from app.models.snapshot import Snapshot
from app.models.device import Device

async def create_tables():
    """Create snapshot table."""
    async with engine.begin() as conn:
        # Create all tables (will skip existing ones)
        await conn.run_sync(Base.metadata.create_all)
        print("Snapshots table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
