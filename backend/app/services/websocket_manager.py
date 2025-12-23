"""
WebSocket Manager for WebRTC Signaling

Handles WebSocket connections for MediaSoup signaling.
"""
from typing import Dict, Set, Any, Optional
from datetime import datetime
from loguru import logger


class WebSocketManager:
    """
    WebSocket Manager for WebRTC signaling.
    
    Manages:
    - WebSocket connections
    - Signaling for MediaSoup
    - Room/channel management
    - ICE candidate exchange
    - Connection state
    """
    
    def __init__(self):
        """Initialize WebSocket Manager."""
        self.connections: Dict[str, Any] = {}  # Connection ID -> Connection info
        self.stream_rooms: Dict[str, Set[str]] = {}  # Stream ID -> Set of connection IDs
        self.connection_rooms: Dict[str, str] = {}  # Connection ID -> Stream ID
        
        logger.info("WebSocket Manager initialized")
    
    async def add_connection(
        self,
        connection_id: str,
        stream_id: str
    ) -> Dict[str, Any]:
        """
        Add a new WebSocket connection.
        
        Args:
            connection_id: Connection identifier
            stream_id: Stream identifier
            
        Returns:
            Connection information
        """
        connection_info = {
            "id": connection_id,
            "stream_id": stream_id,
            "state": "connecting",
            "joined_at": datetime.now(),
            "ice_candidates": []
        }
        
        self.connections[connection_id] = connection_info
        
        # Add to room
        if stream_id not in self.stream_rooms:
            self.stream_rooms[stream_id] = set()
        self.stream_rooms[stream_id].add(connection_id)
        self.connection_rooms[connection_id] = stream_id
        
        logger.info(f"Added connection {connection_id} to stream {stream_id}")
        
        return connection_info
    
    async def remove_connection(self, connection_id: str) -> bool:
        """
        Remove a WebSocket connection.
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            True if removed successfully
        """
        if connection_id not in self.connections:
            return False
        
        # Remove from room
        if connection_id in self.connection_rooms:
            stream_id = self.connection_rooms[connection_id]
            if stream_id in self.stream_rooms:
                self.stream_rooms[stream_id].discard(connection_id)
                if not self.stream_rooms[stream_id]:
                    del self.stream_rooms[stream_id]
            del self.connection_rooms[connection_id]
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"Removed connection {connection_id}")
        return True
    
    async def update_connection_state(
        self,
        connection_id: str,
        state: str
    ) -> bool:
        """
        Update connection state.
        
        Args:
            connection_id: Connection identifier
            state: New state (connecting, connected, disconnected)
            
        Returns:
            True if updated successfully
        """
        if connection_id not in self.connections:
            return False
        
        self.connections[connection_id]["state"] = state
        logger.info(f"Connection {connection_id} state: {state}")
        
        return True
    
    async def add_ice_candidate(
        self,
        connection_id: str,
        candidate: Dict[str, Any]
    ) -> bool:
        """
        Add ICE candidate for a connection.
        
        Args:
            connection_id: Connection identifier
            candidate: ICE candidate data
            
        Returns:
            True if added successfully
        """
        if connection_id not in self.connections:
            return False
        
        self.connections[connection_id]["ice_candidates"].append(candidate)
        logger.debug(f"Added ICE candidate for connection {connection_id}")
        
        return True
    
    async def get_room_connections(self, stream_id: str) -> list:
        """
        Get all connections in a room.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            List of connection IDs
        """
        return list(self.stream_rooms.get(stream_id, set()))
    
    async def get_connection_info(self, connection_id: str) -> Dict[str, Any]:
        """
        Get connection information.
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Connection information
        """
        return self.connections.get(connection_id, {})
    
    async def broadcast_to_room(
        self,
        stream_id: str,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all connections in a room.
        
        Args:
            stream_id: Stream identifier
            message: Message to broadcast
            exclude_connection: Connection ID to exclude
            
        Returns:
            Number of connections notified
        """
        connections = await self.get_room_connections(stream_id)
        
        if exclude_connection:
            connections = [c for c in connections if c != exclude_connection]
        
        logger.info(f"Broadcasting to {len(connections)} connections in stream {stream_id}")
        
        # In real implementation, would send WebSocket messages
        return len(connections)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

