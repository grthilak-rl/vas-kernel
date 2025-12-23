"""
Test utilities and helpers.
"""
from typing import Dict, Any
import uuid
from datetime import datetime


def create_test_device_data(**overrides) -> Dict[str, Any]:
    """Create test device data with optional overrides."""
    return {
        "name": f"Test Camera {uuid.uuid4().hex[:8]}",
        "description": "Test camera description",
        "rtsp_url": f"rtsp://test.example.com/stream/{uuid.uuid4().hex[:8]}",
        "location": "Test Location",
        **overrides
    }


def create_test_stream_data(**overrides) -> Dict[str, Any]:
    """Create test stream data with optional overrides."""
    return {
        "name": f"Test Stream {uuid.uuid4().hex[:8]}",
        "visibility": "private",
        **overrides
    }


def create_test_recording_data(stream_id: str, **overrides) -> Dict[str, Any]:
    """Create test recording data."""
    return {
        "stream_id": stream_id,
        "file_path": f"/recordings/test_{uuid.uuid4().hex[:8]}.ts",
        "duration": 60,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "format": "hls",
        **overrides
    }


def create_test_bookmark_data(stream_id: str, **overrides) -> Dict[str, Any]:
    """Create test bookmark data."""
    return {
        "stream_id": stream_id,
        "name": f"Test Bookmark {uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now().isoformat(),
        "clip_url": f"/recordings/bookmark_{uuid.uuid4().hex[:8]}.mp4",
        "clip_duration": 10,
        **overrides
    }


def create_test_snapshot_data(stream_id: str, **overrides) -> Dict[str, Any]:
    """Create test snapshot data."""
    return {
        "stream_id": stream_id,
        "file_path": f"/snapshots/test_{uuid.uuid4().hex[:8]}.jpg",
        "timestamp": datetime.now().isoformat(),
        "format": "jpg",
        **overrides
    }


def assert_device_response(data: Dict[str, Any]):
    """Assert device response has all required fields."""
    assert "id" in data
    assert "name" in data
    assert "rtsp_url" in data
    assert "is_active" in data
    assert "created_at" in data


def assert_stream_response(data: Dict[str, Any]):
    """Assert stream response has all required fields."""
    assert "id" in data
    assert "device_id" in data
    assert "name" in data
    assert "status" in data
    assert "visibility" in data
    assert "created_at" in data


def assert_error_response(data: Dict[str, Any], expected_error_type: str = None):
    """Assert error response structure."""
    assert "detail" in data
    if expected_error_type:
        assert expected_error_type in str(data["detail"]).lower()


