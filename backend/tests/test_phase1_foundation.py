"""
Phase 1 Tests: Foundation & Infrastructure

Tests for:
- Application startup
- Health check endpoint
- Root endpoint
- Database connection
- Logging configuration
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPhase1Foundation:
    """Phase 1 foundation tests."""
    
    @pytest.mark.phase1
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "VAS Backend"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.phase1
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["version"] == "1.0.0"
    
    @pytest.mark.phase1
    def test_api_docs_accessible(self, client: TestClient):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        
        # Should return HTML page (status 200)
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.phase1
    def test_openapi_schema(self, client: TestClient):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["info"]["title"] == "Video Aggregation Service (VAS)"
        assert data["info"]["version"] == "1.0.0"
        assert "/health" in data["paths"]
        assert "/" in data["paths"]
    
    @pytest.mark.phase1
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers
    
    @pytest.mark.phase1
    def test_non_existent_endpoint(self, client: TestClient):
        """Test 404 handling for non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.phase1
    def test_database_tables_exist(self):
        """Test that database models can be imported and have tables."""
        from app.models import Device, Stream, Recording, Bookmark, Snapshot
        
        # Check that all models have __tablename__
        assert hasattr(Device, "__tablename__")
        assert hasattr(Stream, "__tablename__")
        assert hasattr(Recording, "__tablename__")
        assert hasattr(Bookmark, "__tablename__")
        assert hasattr(Snapshot, "__tablename__")
        
        # Check table names
        assert Device.__tablename__ == "devices"
        assert Stream.__tablename__ == "streams"
        assert Recording.__tablename__ == "recordings"
        assert Bookmark.__tablename__ == "bookmarks"
        assert Snapshot.__tablename__ == "snapshots"
    
    @pytest.mark.phase1
    def test_configuration_loaded(self):
        """Test that configuration is properly loaded."""
        from config import settings
        
        assert settings.database_url is not None
        assert settings.api_port == 8080
        assert settings.websocket_port == 8081
        assert settings.log_level is not None
        assert settings.secret_key is not None
    
    @pytest.mark.phase1
    def test_database_connection(self):
        """Test database connection is configured."""
        from database import engine, Base
        from app.models import Device, Stream, Recording, Bookmark, Snapshot
        
        assert engine is not None
        assert Base is not None
        
        # Import all models to register tables
        assert Device is not None
        assert Stream is not None
        assert Recording is not None
        assert Bookmark is not None
        assert Snapshot is not None
        
        # Verify models exist - this test doesn't require actual DB connection
        # The actual database connection will be tested in integration tests
        assert hasattr(Device, '__tablename__')
        assert hasattr(Stream, '__tablename__')
        assert hasattr(Recording, '__tablename__')
        assert hasattr(Bookmark, '__tablename__')
        assert hasattr(Snapshot, '__tablename__')

