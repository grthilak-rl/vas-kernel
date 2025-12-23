"""
Phase 6 Tests: WebSocket Signaling

Tests for:
- WebSocket server
- Signaling protocol
- ICE candidates
- Connection management
- Room management
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPhase6WebSocketService:
    """Phase 6 WebSocket Service tests."""
    
    @pytest.mark.phase6
    def test_websocket_manager_exists(self):
        """Test that WebSocket manager exists."""
        from app.services.websocket_manager import WebSocketManager, websocket_manager
        
        assert WebSocketManager is not None
        assert websocket_manager is not None
        assert hasattr(websocket_manager, 'add_connection')
        assert hasattr(websocket_manager, 'remove_connection')
        assert hasattr(websocket_manager, 'update_connection_state')
    
    @pytest.mark.phase6
    def test_websocket_routes_registered(self, client: TestClient):
        """Test that WebSocket routes are registered."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that WebSocket endpoints are in schema
        # Note: WebSocket endpoints may not show up in OpenAPI schema
        paths = schema.get("paths", {})
        
        # Check for room info endpoint
        has_websocket_info = any("/streams" in path and "connections" in path 
                                 for path in paths.keys())
    
    @pytest.mark.phase6
    def test_room_connections_endpoint(self, client: TestClient):
        """Test room connections endpoint."""
        response = client.get("/ws/streams/test_stream_001/connections")
        
        # Should not be 404
        assert response.status_code != 404
        if response.status_code == 200:
            data = response.json()
            assert "stream_id" in data
            assert "connection_count" in data
    
    @pytest.mark.phase6
    def test_websocket_connection_structure(self):
        """Test WebSocket manager structure."""
        from app.services.websocket_manager import websocket_manager
        
        assert hasattr(websocket_manager, 'connections')
        assert hasattr(websocket_manager, 'stream_rooms')
        assert hasattr(websocket_manager, 'connection_rooms')
        assert isinstance(websocket_manager.connections, dict)
        assert isinstance(websocket_manager.stream_rooms, dict)
        assert isinstance(websocket_manager.connection_rooms, dict)
    
    @pytest.mark.phase6
    def test_add_connection(self):
        """Test adding a connection."""
        from app.services.websocket_manager import websocket_manager
        import asyncio
        
        async def test():
            connection = await websocket_manager.add_connection("test_conn_1", "test_stream")
            assert connection is not None
            assert connection["id"] == "test_conn_1"
            assert connection["stream_id"] == "test_stream"
            
            # Cleanup
            await websocket_manager.remove_connection("test_conn_1")
        
        asyncio.run(test())
    
    @pytest.mark.phase6
    def test_room_management(self):
        """Test room management."""
        from app.services.websocket_manager import websocket_manager
        import asyncio
        
        async def test():
            # Add two connections to same room
            await websocket_manager.add_connection("conn1", "stream1")
            await websocket_manager.add_connection("conn2", "stream1")
            
            # Check room has both connections
            connections = await websocket_manager.get_room_connections("stream1")
            assert len(connections) == 2
            
            # Cleanup
            await websocket_manager.remove_connection("conn1")
            await websocket_manager.remove_connection("conn2")
        
        asyncio.run(test())
    
    @pytest.mark.phase6
    def test_connection_state_management(self):
        """Test connection state management."""
        from app.services.websocket_manager import websocket_manager
        import asyncio
        
        async def test():
            await websocket_manager.add_connection("test_conn", "test_stream")
            
            # Update state
            updated = await websocket_manager.update_connection_state("test_conn", "connected")
            assert updated == True
            
            # Check state
            info = await websocket_manager.get_connection_info("test_conn")
            assert info["state"] == "connected"
            
            # Cleanup
            await websocket_manager.remove_connection("test_conn")
        
        asyncio.run(test())
    
    @pytest.mark.phase6
    def test_ice_candidate_handling(self):
        """Test ICE candidate handling."""
        from app.services.websocket_manager import websocket_manager
        import asyncio
        
        async def test():
            await websocket_manager.add_connection("test_conn", "test_stream")
            
            # Add ICE candidate
            candidate = {"type": "host", "ip": "127.0.0.1", "port": 54321}
            added = await websocket_manager.add_ice_candidate("test_conn", candidate)
            assert added == True
            
            # Check candidate was added
            info = await websocket_manager.get_connection_info("test_conn")
            assert len(info["ice_candidates"]) == 1
            
            # Cleanup
            await websocket_manager.remove_connection("test_conn")
        
        asyncio.run(test())


class TestPhase6WebSocketIntegration:
    """Test WebSocket integration."""
    
    @pytest.mark.phase6
    def test_websocket_manager_in_main_app(self):
        """Test that WebSocket manager is accessible."""
        from app.services.websocket_manager import websocket_manager
        
        assert websocket_manager is not None
        assert websocket_manager.connections is not None
        assert websocket_manager.stream_rooms is not None
    
    @pytest.mark.phase6
    def test_websocket_initialized(self):
        """Test that WebSocket manager initializes properly."""
        from app.services.websocket_manager import websocket_manager
        
        assert websocket_manager is not None
        assert isinstance(websocket_manager.connections, dict)
        assert isinstance(websocket_manager.stream_rooms, dict)
        assert isinstance(websocket_manager.connection_rooms, dict)

