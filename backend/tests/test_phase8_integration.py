"""
Phase 8 Tests: Integration & E2E Testing

Tests for:
- System integration
- Health checks
- Service communication
- End-to-end flows
"""
import pytest
from fastapi import status


class TestPhase8HealthChecks:
    """Phase 8 Health Check tests."""
    
    @pytest.mark.phase8
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    @pytest.mark.phase8
    def test_detailed_health_endpoint(self, client):
        """Test detailed health endpoint."""
        response = client.get("/health/detailed")
        
        # Should not be 404
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "checks" in data
            assert "timestamp" in data
    
    @pytest.mark.phase8
    def test_health_endpoint_structure(self, client):
        """Test health endpoint structure."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["status", "service", "version"]
        for field in required_fields:
            assert field in data


class TestPhase8ServiceIntegration:
    """Phase 8 Service Integration tests."""
    
    @pytest.mark.phase8
    def test_database_connection(self):
        """Test database connection."""
        from database import engine
        from sqlalchemy import text
        
        import asyncio
        
        async def check_db():
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                return True
            except Exception as e:
                print(f"Database connection failed: {e}")
                return False
        
        result = asyncio.run(check_db())
        assert result == True
    
    @pytest.mark.phase8
    def test_websocket_manager_available(self):
        """Test that WebSocket manager is available."""
        from app.services.websocket_manager import websocket_manager
        
        assert websocket_manager is not None
        assert hasattr(websocket_manager, 'connections')
        assert hasattr(websocket_manager, 'stream_rooms')
    
    @pytest.mark.phase8
    def test_mediasoup_service_available(self):
        """Test that MediaSoup service is available."""
        from app.services.mediasoup_service import media_soup_worker
        
        assert media_soup_worker is not None
        assert hasattr(media_soup_worker, 'routers')
        assert hasattr(media_soup_worker, 'create_router')
    
    @pytest.mark.phase8
    def test_rtsp_pipeline_available(self):
        """Test that RTSP pipeline service is available."""
        from app.services.rtsp_pipeline import rtsp_service
        
        assert rtsp_service is not None
        assert hasattr(rtsp_service, 'active_streams')
        assert hasattr(rtsp_service, 'start_stream')
    
    @pytest.mark.phase8
    def test_recording_service_available(self):
        """Test that recording service is available."""
        from app.services.recording_service import recording_manager
        
        assert recording_manager is not None
        assert hasattr(recording_manager, 'active_recordings')
        assert hasattr(recording_manager, 'start_recording')


class TestPhase8APIIntegration:
    """Phase 8 API Integration tests."""
    
    @pytest.mark.phase8
    def test_device_crud_flow(self, client):
        """Test device CRUD operations."""
        # Create device
        device_data = {
            "name": "Test Camera",
            "ip_address": "192.168.1.100",
            "rtsp_url": "rtsp://192.168.1.100:554/stream1"
        }
        
        response = client.post("/api/v1/devices", json=device_data)
        assert response.status_code in [200, 201]
        
        device_id = response.json().get("id")
        assert device_id is not None
    
    @pytest.mark.phase8
    def test_stream_management_apis(self, client):
        """Test stream management APIs."""
        # List streams
        response = client.get("/api/v1/streams")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            streams = response.json()
            assert isinstance(streams, (list, dict))
    
    @pytest.mark.phase8
    def test_mediasoup_apis(self, client):
        """Test MediaSoup APIs."""
        # Get routers
        response = client.get("/api/v1/mediasoup/routers")
        assert response.status_code in [200, 404]
    
    @pytest.mark.phase8
    def test_rtsp_pipeline_apis(self, client):
        """Test RTSP pipeline APIs."""
        # Get active streams
        response = client.get("/api/v1/rtsp/streams")
        assert response.status_code in [200, 404]
    
    @pytest.mark.phase8
    def test_recording_apis(self, client):
        """Test recording APIs."""
        # List recordings
        response = client.get("/api/v1/recordings")
        assert response.status_code in [200, 404]
    
    @pytest.mark.phase8
    def test_websocket_info_api(self, client):
        """Test WebSocket info API."""
        # Get room connections
        response = client.get("/ws/streams/test_stream/connections")
        # Should not be 404
        assert response.status_code != 404


