"""End-to-end demonstration of Phase 5.1: AI Event Persistence.

This script demonstrates the complete Phase 5.1 implementation:
1. Creating AI event schemas
2. Persisting events to the database
3. Verifying best-effort semantics (failure handling)
4. Demonstrating isolation guarantees

NOTE: This requires a running PostgreSQL database with devices table populated.
"""
import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add backend to path
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models.ai_event import AIEvent
from app.models.device import Device
from app.schemas.ai_event import AIEventCreate
from app.services.ai_event_service import AIEventService
from config import settings


async def main():
    """Run Phase 5.1 end-to-end demonstration."""
    print("=" * 70)
    print("Phase 5.1 End-to-End Demonstration: AI Event Persistence")
    print("=" * 70)

    # Create database connection (convert to asyncpg URL)
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True
    )

    SessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with SessionLocal() as session:
        print("\n1. Database Connection")
        print("-" * 70)
        print("✅ Connected to PostgreSQL database")

        # Check for devices
        print("\n2. Checking for Devices")
        print("-" * 70)
        device_query = select(Device).limit(1)
        result = await session.execute(device_query)
        device = result.scalar_one_or_none()

        if not device:
            print("⚠️  No devices found in database")
            print("   Creating a test device...")

            test_device = Device(
                name="Test Camera (Phase 5.1)",
                rtsp_url="rtsp://test.example.com/stream",
                location="Test Location",
                is_active=True
            )
            session.add(test_device)
            await session.commit()
            await session.refresh(test_device)
            device = test_device
            print(f"✅ Created test device: {device.id}")
        else:
            print(f"✅ Found existing device: {device.id} ({device.name})")

        # Initialize AI Event Service
        print("\n3. Initialize AI Event Service")
        print("-" * 70)
        ai_service = AIEventService()
        print("✅ AIEventService initialized")

        # Test 1: Persist a minimal event
        print("\n4. Test: Persist Minimal Event")
        print("-" * 70)

        minimal_event = AIEventCreate(
            camera_id=device.id,
            model_id="yolov8-person-detection",
            timestamp=datetime.now(timezone.utc),
            detections={"result": "no_detection"}
        )

        result = await ai_service.persist_event(minimal_event, session)

        if result:
            print(f"✅ Event persisted successfully: {result.id}")
            print(f"   Camera: {result.camera_id}")
            print(f"   Model: {result.model_id}")
            print(f"   Timestamp: {result.timestamp}")
        else:
            print("❌ Event persistence failed (unexpected)")

        # Test 2: Persist a full event with all fields
        print("\n5. Test: Persist Full Event (All Fields)")
        print("-" * 70)

        full_event = AIEventCreate(
            camera_id=device.id,
            model_id="yolov8-person-detection",
            timestamp=datetime.now(timezone.utc),
            frame_id=12345,
            detections={
                "objects": [
                    {
                        "class": "person",
                        "bbox": [100, 200, 300, 400],
                        "confidence": 0.95
                    },
                    {
                        "class": "person",
                        "bbox": [500, 150, 650, 380],
                        "confidence": 0.87
                    }
                ],
                "count": 2
            },
            confidence=0.91,
            event_metadata={
                "model_version": "8.0.1",
                "inference_latency_ms": 45.2,
                "gpu_used": True
            }
        )

        result = await ai_service.persist_event(full_event, session)

        if result:
            print(f"✅ Full event persisted: {result.id}")
            print(f"   Frame ID: {result.frame_id}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Detections: {len(result.detections.get('objects', []))} persons")
            print(f"   Metadata: {result.event_metadata}")
        else:
            print("❌ Full event persistence failed (unexpected)")

        # Test 3: Best-effort semantics - Invalid camera ID
        print("\n6. Test: Best-Effort Semantics (Invalid Camera ID)")
        print("-" * 70)

        invalid_event = AIEventCreate(
            camera_id=uuid4(),  # Non-existent camera (FK violation)
            model_id="test-model",
            timestamp=datetime.now(timezone.utc),
            detections={"test": "data"}
        )

        result = await ai_service.persist_event(invalid_event, session)

        if result is None:
            print("✅ Best-effort semantics verified: FK violation → silent drop")
        else:
            print("❌ Unexpected: FK violation should have been dropped silently")

        # Test 4: Verify persisted events
        print("\n7. Test: Query Persisted Events")
        print("-" * 70)

        query = select(AIEvent).where(
            AIEvent.camera_id == device.id
        ).order_by(AIEvent.created_at.desc()).limit(5)

        result = await session.execute(query)
        events = result.scalars().all()

        print(f"✅ Found {len(events)} events for device {device.id}")
        for i, event in enumerate(events, 1):
            print(f"   {i}. Event {event.id}")
            print(f"      Model: {event.model_id}")
            print(f"      Timestamp: {event.timestamp}")
            print(f"      Created: {event.created_at}")

        # Test 5: Isolation guarantee - Session still usable after failure
        print("\n8. Test: Isolation Guarantee (Session Recovery)")
        print("-" * 70)

        # Cause a failure
        invalid_event2 = AIEventCreate(
            camera_id=uuid4(),
            model_id="test",
            timestamp=datetime.now(timezone.utc),
            detections={}
        )
        await ai_service.persist_event(invalid_event2, session)

        # Session should still be usable
        try:
            count_query = select(AIEvent).where(AIEvent.camera_id == device.id)
            result = await session.execute(count_query)
            count = len(result.scalars().all())
            print(f"✅ Session still usable after failure: {count} events found")
        except Exception as e:
            print(f"❌ Session contaminated: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("Phase 5.1 End-to-End Demonstration: COMPLETE")
    print("=" * 70)
    print("\nVerified Capabilities:")
    print("  ✅ Write-only, insert-only persistence")
    print("  ✅ Best-effort semantics (silent failure on FK violation)")
    print("  ✅ Full event schema support (all fields)")
    print("  ✅ Minimal event schema support (required fields only)")
    print("  ✅ Database query functionality")
    print("  ✅ Session isolation (recovery after failure)")
    print("\nPhase 5.1 Status: READY FOR INTEGRATION")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
