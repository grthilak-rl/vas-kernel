"""
Phase 5 Tests: Recording Service

Tests for:
- Recording service
- HLS recording
- Bookmark creation
- Snapshot capture
- Segment management
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime


class TestPhase5RecordingService:
    """Phase 5 Recording Service tests."""
    
    @pytest.mark.phase5
    def test_recording_service_exists(self):
        """Test that recording service exists."""
        from app.services.recording_service import RecordingService, recording_service
        
        assert RecordingService is not None
        assert recording_service is not None
        assert hasattr(recording_service, 'start_recording')
        assert hasattr(recording_service, 'create_bookmark')
        assert hasattr(recording_service, 'capture_snapshot')
    
    @pytest.mark.phase5
    def test_recording_routes_registered(self, client: TestClient):
        """Test that recording routes are registered."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that recording endpoints are in schema
        paths = schema.get("paths", {})
        recording_paths = [path for path in paths.keys() if "/recordings" in path]
        
        assert len(recording_paths) > 0, "Recording endpoints not found in OpenAPI schema"
    
    @pytest.mark.phase5
    def test_start_recording_api(self, client: TestClient):
        """Test start recording endpoint."""
        response = client.post(
            "/api/v1/recordings/streams/test_stream_001/start"
        )
        
        # Should not be 404
        assert response.status_code != 404
        assert response.status_code in [200, 201, 422]
    
    @pytest.mark.phase5
    def test_stop_recording_api(self, client: TestClient):
        """Test stop recording endpoint."""
        response = client.post(
            "/api/v1/recordings/streams/test_stream_001/stop"
        )
        
        # 404 is expected for non-existent recording
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase5
    def test_get_recording_info_api(self, client: TestClient):
        """Test get recording info endpoint."""
        response = client.get(
            "/api/v1/recordings/streams/test_stream_001"
        )
        
        # 404 is expected for non-existent recording
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase5
    def test_create_bookmark_api(self, client: TestClient):
        """Test create bookmark endpoint."""
        response = client.post(
            "/api/v1/recordings/streams/test_stream_001/bookmarks",
            params={
                "name": "test_bookmark",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 404 is expected for non-existent recording
        assert response.status_code in [404, 200, 422]
    
    @pytest.mark.phase5
    def test_capture_snapshot_api(self, client: TestClient):
        """Test capture snapshot endpoint."""
        response = client.post(
            "/api/v1/recordings/streams/test_stream_001/snapshot"
        )
        
        # Should not be 404
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    @pytest.mark.phase5
    def test_cleanup_segments_api(self, client: TestClient):
        """Test cleanup segments endpoint."""
        response = client.post(
            "/api/v1/recordings/streams/test_stream_001/cleanup"
        )
        
        # 404 is expected for non-existent recording
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase5
    def test_list_active_recordings_api(self, client: TestClient):
        """Test list active recordings endpoint."""
        response = client.get("/api/v1/recordings/streams")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_recordings" in data


class TestPhase5RecordingStructure:
    """Test Recording Service structure."""
    
    @pytest.mark.phase5
    def test_recording_service_has_active_recordings_dict(self):
        """Test that service has active_recordings dictionary."""
        from app.services.recording_service import recording_service
        
        assert hasattr(recording_service, 'active_recordings')
        assert isinstance(recording_service.active_recordings, dict)
    
    @pytest.mark.phase5
    def test_recording_service_has_config(self):
        """Test that service has configuration."""
        from app.services.recording_service import recording_service
        
        assert hasattr(recording_service, 'hls_segment_duration')
        assert hasattr(recording_service, 'retention_days')
        assert recording_service.hls_segment_duration == 10
        assert recording_service.retention_days == 7


class TestPhase5RecordingIntegration:
    """Test Recording Service integration."""
    
    @pytest.mark.phase5
    def test_recording_routes_in_main_app(self):
        """Test that recording routes are registered in main app."""
        from main import app
        
        # Check if recording router is included
        route_paths = [route.path for route in app.routes]
        recording_routes = [path for path in route_paths if 'recordings' in path]
        
        assert len(recording_routes) > 0, "Recording routes not found in main app"
    
    @pytest.mark.phase5
    def test_recording_service_initialized(self):
        """Test that recording service initializes properly."""
        from app.services.recording_service import recording_service
        
        assert recording_service is not None
        assert isinstance(recording_service.active_recordings, dict)
        assert recording_service.hls_segment_duration == 10


