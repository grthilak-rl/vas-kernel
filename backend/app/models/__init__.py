"""Database models."""
from app.models.device import Device
from app.models.stream import Stream
from app.models.recording import Recording
from app.models.bookmark import Bookmark
from app.models.snapshot import Snapshot
from app.models.api_key import ApiKey
from app.models.ai_event import AIEvent
from app.models.ai_model_assignment import AIModelAssignment

__all__ = [
    "Device",
    "Stream",
    "Recording",
    "Bookmark",
    "Snapshot",
    "ApiKey",
    "AIEvent",
    "AIModelAssignment",
]
