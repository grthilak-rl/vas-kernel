"""
Phase 4 Tests: RTSP Pipeline

Tests for:
- RTSP pipeline service
- Stream management
- Health monitoring
- Auto-reconnection
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPhase4RTSPPipeline:
    """Phase 4 RTSP Pipeline tests."""
    
    @pytest.mark.phase4
    def test_rtsp_pipeline_service_exists(self):
        """Test that RTSP pipeline service exists."""
        from app.services.rtsp_pipeline import RTSPPipeline, rtsp_pipeline
        
        assert RTSPPipeline is not None
        assert rtsp_pipeline is not None
        assert hasattr(rtsp_pipeline, 'start_stream')
        assert hasattr(rtsp_pipeline, 'stop_stream')
        assert hasattr(rtsp_pipeline, 'check_stream_health')
    
    @pytest.mark.phase4
    def test_rtsp_routes_registered(self, client: TestClient):
        """Test that RTSP routes are registered."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that RTSP endpoints are in schema
        paths = schema.get("paths", {})
        rtsp_paths = [path for path in paths.keys() if "/rtsp" in path]
        
        assert len(rtsp_paths) > 0, "RTSP endpoints not found in OpenAPI schema"
    
    @pytest.mark.phase4
    def test_start_rtsp_stream_api(self, client: TestClient):
        """Test start RTSP stream endpoint."""
        response = client.post(
            "/api/v1/rtsp/streams/test_stream_001/start",
            params={
                "rtsp_url": "rtsp://test.example.com/stream",
                "rtp_params": '{"ip":"127.0.0.1","port":40000}'
            }
        )
        
        # Should not be 404
        assert response.status_code != 404
        assert response.status_code in [200, 201, 422]
    
    @pytest.mark.phase4
    def test_stop_rtsp_stream_api(self, client: TestClient):
        """Test stop RTSP stream endpoint."""
        response = client.post(
            "/api/v1/rtsp/streams/test_stream_001/stop"
        )
        
        # 404 is expected for non-existent stream
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase4
    def test_check_stream_health_api(self, client: TestClient):
        """Test stream health check endpoint."""
        response = client.get(
            "/api/v1/rtsp/streams/test_stream_001/health"
        )
        
        # 404 is expected for non-existent stream
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase4
    def test_get_stream_stats_api(self, client: TestClient):
        """Test get stream stats endpoint."""
        response = client.get(
            "/api/v1/rtsp/streams/test_stream_001/stats"
        )
        
        # 404 is expected for non-existent stream
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase4
    def test_reconnect_stream_api(self, client: TestClient):
        """Test reconnect stream endpoint."""
        response = client.post(
            "/api/v1/rtsp/streams/test_stream_001/reconnect"
        )
        
        # 404 is expected for non-existent stream
        assert response.status_code in [404, 200]
    
    @pytest.mark.phase4
    def test_list_active_streams_api(self, client: TestClient):
        """Test list active streams endpoint."""
        response = client.get("/api/v1/rtsp/streams")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_streams" in data


class TestPhase4RTSPStructure:
    """Test RTSP Pipeline structure."""
    
    @pytest.mark.phase4
    def test_rtsp_pipeline_has_active_streams_dict(self):
        """Test that pipeline has active_streams dictionary."""
        from app.services.rtsp_pipeline import rtsp_pipeline
        
        assert hasattr(rtsp_pipeline, 'active_streams')
        assert isinstance(rtsp_pipeline.active_streams, dict)
    
    @pytest.mark.phase4
    def test_rtsp_pipeline_has_ffmpeg_processes_dict(self):
        """Test that pipeline has ffmpeg_processes dictionary."""
        from app.services.rtsp_pipeline import rtsp_pipeline
        
        assert hasattr(rtsp_pipeline, 'ffmpeg_processes')
        assert isinstance(rtsp_pipeline.ffmpeg_processes, dict)


class TestPhase4RTSPIntegration:
    """Test RTSP Pipeline integration."""
    
    @pytest.mark.phase4
    def test_rtsp_routes_in_main_app(self):
        """Test that RTSP routes are registered in main app."""
        from main import app
        
        # Check if RTSP router is included
        route_paths = [route.path for route in app.routes]
        rtsp_routes = [path for path in route_paths if 'rtsp' in path]
        
        assert len(rtsp_routes) > 0, "RTSP routes not found in main app"
    
    @pytest.mark.phase4
    def test_rtsp_pipeline_initialized(self):
        """Test that RTSP pipeline initializes properly."""
        from app.services.rtsp_pipeline import rtsp_pipeline
        
        assert rtsp_pipeline is not None
        assert isinstance(rtsp_pipeline.active_streams, dict)
        assert isinstance(rtsp_pipeline.ffmpeg_processes, dict)

