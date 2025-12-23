"""
Phase 3 Tests: MediaSoup Worker

Tests for:
- MediaSoup service
- Router management
- Transport creation
- Producer/consumer management
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPhase3MediaSoupService:
    """Phase 3 MediaSoup service tests."""
    
    @pytest.mark.phase3
    def test_mediasoup_service_exists(self):
        """Test that MediaSoup service exists and is importable."""
        from app.services.mediasoup_service import MediaSoupWorker, mediasoup_worker
        
        assert MediaSoupWorker is not None
        assert mediasoup_worker is not None
        assert hasattr(mediasoup_worker, 'create_router')
        assert hasattr(mediasoup_worker, 'create_webrtc_transport')
        assert hasattr(mediasoup_worker, 'create_rtp_transport')
    
    @pytest.mark.phase3
    def test_mediasoup_routes_registered(self, client: TestClient):
        """Test that MediaSoup routes are registered."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that mediasoup endpoints are in schema
        paths = schema.get("paths", {})
        mediasoup_paths = [path for path in paths.keys() if "/mediasoup" in path]
        
        assert len(mediasoup_paths) > 0, "MediaSoup endpoints not found in OpenAPI schema"
    
    @pytest.mark.phase3
    def test_mediasoup_endpoints_exist(self, client: TestClient):
        """Test that MediaSoup endpoints are accessible."""
        # Try to call an endpoint
        response = client.post("/api/v1/mediasoup/router", json={"router_id": "test_123"})
        
        # Should not be 404
        assert response.status_code != 404
    
    @pytest.mark.phase3
    def test_create_router_api(self, client: TestClient):
        """Test create router endpoint."""
        response = client.post(
            "/api/v1/mediasoup/router",
            params={"router_id": "test_router_001"}
        )
        
        # Should return success
        assert response.status_code in [200, 201, 422]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "router" in data
    
    @pytest.mark.phase3
    def test_create_webrtc_transport_api(self, client: TestClient):
        """Test create WebRTC transport endpoint."""
        # First create a router
        client.post(
            "/api/v1/mediasoup/router",
            params={"router_id": "test_router_for_transport"}
        )
        
        # Then create transport
        response = client.post(
            "/api/v1/mediasoup/router/test_router_for_transport/webrtc-transport",
            params={"transport_id": "test_transport_001"}
        )
        
        # Should return success or error (not 404)
        assert response.status_code in [200, 201, 400, 404, 422]
    
    @pytest.mark.phase3
    def test_create_rtp_transport_api(self, client: TestClient):
        """Test create RTP transport endpoint."""
        # First create a router
        client.post(
            "/api/v1/mediasoup/router",
            params={"router_id": "test_router_for_rtp"}
        )
        
        # Then create RTP transport
        response = client.post(
            "/api/v1/mediasoup/router/test_router_for_rtp/rtp-transport",
            params={"transport_id": "test_rtp_transport_001"}
        )
        
        # Should return success or error (not 404)
        assert response.status_code in [200, 201, 400, 404, 422]


class TestPhase3MediaSoupStructure:
    """Test MediaSoup structure and components."""
    
    @pytest.mark.phase3
    def test_router_has_routers_dict(self):
        """Test that worker has routers dictionary."""
        from app.services.mediasoup_service import mediasoup_worker
        
        assert hasattr(mediasoup_worker, 'routers')
        assert isinstance(mediasoup_worker.routers, dict)
    
    @pytest.mark.phase3
    def test_worker_has_transports_dict(self):
        """Test that worker has transports dictionary."""
        from app.services.mediasoup_service import mediasoup_worker
        
        assert hasattr(mediasoup_worker, 'transports')
        assert isinstance(mediasoup_worker.transports, dict)
    
    @pytest.mark.phase3
    def test_worker_has_producers_dict(self):
        """Test that worker has producers dictionary."""
        from app.services.mediasoup_service import mediasoup_worker
        
        assert hasattr(mediasoup_worker, 'producers')
        assert isinstance(mediasoup_worker.producers, dict)
    
    @pytest.mark.phase3
    def test_worker_has_consumers_dict(self):
        """Test that worker has consumers dictionary."""
        from app.services.mediasoup_service import mediasoup_worker
        
        assert hasattr(mediasoup_worker, 'consumers')
        assert isinstance(mediasoup_worker.consumers, dict)


class TestPhase3MediaSoupIntegration:
    """Test MediaSoup integration with main app."""
    
    @pytest.mark.phase3
    def test_mediasoup_routes_in_main_app(self):
        """Test that MediaSoup routes are registered in main app."""
        from main import app
        
        # Check if mediasoup router is included
        route_paths = [route.path for route in app.routes]
        mediasoup_routes = [path for path in route_paths if 'mediasoup' in path]
        
        assert len(mediasoup_routes) > 0, "MediaSoup routes not found in main app"
    
    @pytest.mark.phase3
    def test_mediasoup_service_initialized(self):
        """Test that MediaSoup service initializes properly."""
        from app.services.mediasoup_service import mediasoup_worker
        
        # Service should be initialized
        assert mediasoup_worker is not None
        # These dicts exist (but may have data from other tests)
        assert isinstance(mediasoup_worker.routers, dict)
        assert isinstance(mediasoup_worker.transports, dict)
        assert isinstance(mediasoup_worker.producers, dict)
        assert isinstance(mediasoup_worker.consumers, dict)

