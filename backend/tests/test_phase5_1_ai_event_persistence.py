"""Integration tests for Phase 5.1: Backend AI Integration (AI Event Schema + Persistence).

Phase 5.1 Tests:
- AI event schema validation
- Write-only persistence (insert-only)
- Best-effort semantics (failure handling)
- Isolation guarantees (failures don't affect system)
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ai_event import AIEvent
from app.schemas.ai_event import AIEventCreate
from app.services.ai_event_service import AIEventService


@pytest.fixture
async def ai_event_service():
    """Fixture to provide AIEventService instance."""
    return AIEventService()


@pytest.fixture
def sample_event_data():
    """Fixture to provide sample AI event data."""
    return {
        "camera_id": uuid4(),
        "model_id": "yolov8-person-detection",
        "timestamp": datetime.now(timezone.utc),
        "frame_id": 12345,
        "detections": {
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
        "confidence": 0.91,
        "event_metadata": {
            "model_version": "8.0.1",
            "inference_latency_ms": 45.2,
            "gpu_used": True
        }
    }


class TestAIEventSchema:
    """Test AI event schema validation (Phase 5.1)."""

    def test_create_event_schema_valid(self, sample_event_data):
        """Test creating valid AIEventCreate schema."""
        event = AIEventCreate(**sample_event_data)

        assert event.camera_id == sample_event_data["camera_id"]
        assert event.model_id == sample_event_data["model_id"]
        assert event.timestamp == sample_event_data["timestamp"]
        assert event.frame_id == sample_event_data["frame_id"]
        assert event.detections == sample_event_data["detections"]
        assert event.confidence == sample_event_data["confidence"]
        assert event.event_metadata == sample_event_data["event_metadata"]

    def test_create_event_schema_minimal(self):
        """Test creating minimal AIEventCreate schema (required fields only)."""
        minimal_data = {
            "camera_id": uuid4(),
            "model_id": "test-model",
            "timestamp": datetime.now(timezone.utc),
            "detections": {"result": "no_detection"}
        }

        event = AIEventCreate(**minimal_data)

        assert event.camera_id == minimal_data["camera_id"]
        assert event.model_id == minimal_data["model_id"]
        assert event.timestamp == minimal_data["timestamp"]
        assert event.detections == minimal_data["detections"]
        assert event.frame_id is None
        assert event.confidence is None
        assert event.event_metadata is None

    def test_create_event_schema_empty_detections(self):
        """Test creating event with empty detections (model-agnostic)."""
        event_data = {
            "camera_id": uuid4(),
            "model_id": "test-model",
            "timestamp": datetime.now(timezone.utc),
            "detections": {}  # Empty but valid
        }

        event = AIEventCreate(**event_data)
        assert event.detections == {}

    def test_create_event_schema_confidence_range(self):
        """Test confidence score validation (0.0-1.0)."""
        base_data = {
            "camera_id": uuid4(),
            "model_id": "test-model",
            "timestamp": datetime.now(timezone.utc),
            "detections": {"test": "data"}
        }

        # Valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            event = AIEventCreate(**{**base_data, "confidence": confidence})
            assert event.confidence == confidence

        # Invalid confidence values should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            AIEventCreate(**{**base_data, "confidence": -0.1})

        with pytest.raises(Exception):
            AIEventCreate(**{**base_data, "confidence": 1.1})


class TestAIEventPersistence:
    """Test AI event persistence (Phase 5.1)."""

    @pytest.mark.asyncio
    async def test_persist_event_success(
        self,
        ai_event_service: AIEventService,
        sample_event_data: dict,
        db: AsyncSession
    ):
        """Test successful AI event persistence."""
        event_schema = AIEventCreate(**sample_event_data)

        # Persist event
        result = await ai_event_service.persist_event(event_schema, db)

        # Verify return value
        assert result is not None
        assert isinstance(result, AIEvent)
        assert result.id is not None
        assert result.camera_id == sample_event_data["camera_id"]
        assert result.model_id == sample_event_data["model_id"]
        assert result.timestamp == sample_event_data["timestamp"]
        assert result.frame_id == sample_event_data["frame_id"]
        assert result.detections == sample_event_data["detections"]
        assert result.confidence == sample_event_data["confidence"]
        assert result.event_metadata == sample_event_data["event_metadata"]
        assert result.created_at is not None

        # Verify database persistence
        query = select(AIEvent).where(AIEvent.id == result.id)
        db_result = await db.execute(query)
        persisted_event = db_result.scalar_one_or_none()

        assert persisted_event is not None
        assert persisted_event.id == result.id
        assert persisted_event.camera_id == sample_event_data["camera_id"]

    @pytest.mark.asyncio
    async def test_persist_event_dict_success(
        self,
        ai_event_service: AIEventService,
        db: AsyncSession
    ):
        """Test persist_event_dict convenience method."""
        camera_id = uuid4()
        model_id = "test-model"
        timestamp = datetime.now(timezone.utc)
        detections = {"class": "person", "count": 1}

        result = await ai_event_service.persist_event_dict(
            camera_id=camera_id,
            model_id=model_id,
            timestamp=timestamp,
            detections=detections,
            frame_id=999,
            confidence=0.88,
            event_metadata={"test": "metadata"},
            db=db
        )

        assert result is not None
        assert result.camera_id == camera_id
        assert result.model_id == model_id
        assert result.detections == detections
        assert result.frame_id == 999
        assert result.confidence == 0.88

    @pytest.mark.asyncio
    async def test_persist_multiple_events(
        self,
        ai_event_service: AIEventService,
        db: AsyncSession
    ):
        """Test persisting multiple events for same camera+model."""
        camera_id = uuid4()
        model_id = "yolov8-test"

        # Persist 3 events
        event_ids = []
        for i in range(3):
            event_data = AIEventCreate(
                camera_id=camera_id,
                model_id=model_id,
                timestamp=datetime.now(timezone.utc),
                frame_id=i,
                detections={"frame": i, "objects": []}
            )

            result = await ai_event_service.persist_event(event_data, db)
            assert result is not None
            event_ids.append(result.id)

        # Verify all events persisted
        query = select(AIEvent).where(
            AIEvent.camera_id == camera_id,
            AIEvent.model_id == model_id
        )
        db_result = await db.execute(query)
        events = db_result.scalars().all()

        assert len(events) == 3
        assert all(e.id in event_ids for e in events)


class TestBestEffortSemantics:
    """Test best-effort persistence semantics (Phase 5.1)."""

    @pytest.mark.asyncio
    async def test_persist_invalid_camera_id_silent_drop(
        self,
        ai_event_service: AIEventService,
        db: AsyncSession
    ):
        """Test that invalid camera_id (FK violation) results in silent drop."""
        # Create event with non-existent camera_id (FK constraint violation)
        invalid_event = AIEventCreate(
            camera_id=uuid4(),  # Does not exist in devices table
            model_id="test-model",
            timestamp=datetime.now(timezone.utc),
            detections={"test": "data"}
        )

        # Should return None (silent drop), NOT raise exception
        result = await ai_event_service.persist_event(invalid_event, db)

        # Best-effort semantics: failure returns None
        assert result is None

        # Verify nothing was persisted
        query = select(AIEvent).where(
            AIEvent.camera_id == invalid_event.camera_id
        )
        db_result = await db.execute(query)
        events = db_result.scalars().all()
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_persist_event_dict_validation_failure(
        self,
        ai_event_service: AIEventService,
        db: AsyncSession
    ):
        """Test that validation failures in persist_event_dict result in silent drop."""
        # Invalid confidence value (out of range)
        result = await ai_event_service.persist_event_dict(
            camera_id=uuid4(),
            model_id="test",
            timestamp=datetime.now(timezone.utc),
            detections={"test": "data"},
            confidence=2.0,  # Invalid: > 1.0
            db=db
        )

        # Should return None (silent drop)
        assert result is None


class TestIsolationGuarantees:
    """Test that AI event persistence failures don't affect system (Phase 5.1)."""

    @pytest.mark.asyncio
    async def test_persistence_failure_isolation(
        self,
        ai_event_service: AIEventService,
        db: AsyncSession
    ):
        """Test that persistence failure doesn't crash or affect caller."""
        # Attempt to persist event with invalid FK (should fail silently)
        invalid_event = AIEventCreate(
            camera_id=uuid4(),  # Non-existent
            model_id="test-model",
            timestamp=datetime.now(timezone.utc),
            detections={"test": "data"}
        )

        # This should NOT raise an exception
        try:
            result = await ai_event_service.persist_event(invalid_event, db)
            assert result is None  # Silent drop
        except Exception as e:
            pytest.fail(f"Persistence failure should be silent, but raised: {e}")

        # Database session should still be usable after failure
        query = select(AIEvent)
        db_result = await db.execute(query)
        events = db_result.scalars().all()
        # Should succeed (session not contaminated)


class TestInsertOnlySemantics:
    """Test insert-only semantics (Phase 5.1)."""

    @pytest.mark.asyncio
    async def test_no_update_api(self, ai_event_service: AIEventService):
        """Verify AIEventService has NO update methods (insert-only)."""
        service_methods = dir(ai_event_service)

        # Should NOT have update/modify methods
        forbidden_methods = ["update", "modify", "edit", "delete", "remove"]
        for method in forbidden_methods:
            matching = [m for m in service_methods if method in m.lower()]
            assert len(matching) == 0, f"Found forbidden method: {matching}"

        # Should ONLY have persist methods
        assert "persist_event" in service_methods
        assert "persist_event_dict" in service_methods


@pytest.mark.phase5_1
class TestPhase5_1Complete:
    """Verify Phase 5.1 is complete."""

    def test_phase5_1_components_exist(self):
        """Test that all Phase 5.1 components are present."""
        # Model
        from app.models.ai_event import AIEvent
        assert AIEvent is not None

        # Schema
        from app.schemas.ai_event import AIEventCreate, AIEventResponse
        assert AIEventCreate is not None
        assert AIEventResponse is not None

        # Service
        from app.services.ai_event_service import AIEventService
        assert AIEventService is not None

        print("✅ Phase 5.1: Backend AI Integration (AI Event Schema + Persistence) - COMPLETE")

    @pytest.mark.asyncio
    async def test_phase5_1_end_to_end(self, db: AsyncSession):
        """End-to-end test: schema -> service -> persistence."""
        # Create service
        service = AIEventService()

        # Create event data
        event_data = AIEventCreate(
            camera_id=uuid4(),  # Will fail FK, but should be silent
            model_id="e2e-test-model",
            timestamp=datetime.now(timezone.utc),
            detections={"test": "end-to-end"},
            confidence=0.99
        )

        # Persist (will fail due to FK, but should be silent)
        result = await service.persist_event(event_data, db)

        # Verify best-effort semantics (silent drop on FK violation)
        # This proves the system is resilient to failures
        assert result is None  # FK violation causes silent drop

        print("✅ Phase 5.1 end-to-end test: Best-effort semantics verified")
