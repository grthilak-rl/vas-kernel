"""
WebSocket signaling routes for WebRTC.
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException, status
from typing import Dict, Any
from loguru import logger
from app.services.websocket_manager import websocket_manager
import json

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/signaling/{stream_id}")
async def websocket_signaling(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint for MediaSoup signaling.
    
    Handles:
    - Producer/consumer negotiation
    - ICE candidate exchange
    - Transport parameters
    """
    connection_id = f"{stream_id}_{id(websocket)}"
    
    # Accept connection
    await websocket.accept()
    
    # Add to manager
    await websocket_manager.add_connection(connection_id, stream_id)
    
    logger.info(f"New WebSocket connection: {connection_id} for stream {stream_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            # Handle different message types
            if msg_type == "connect":
                await websocket_manager.update_connection_state(connection_id, "connected")
                await websocket.send_json({
                    "type": "connected",
                    "connection_id": connection_id,
                    "stream_id": stream_id
                })
            
            elif msg_type == "ice_candidate":
                candidate = message.get("candidate")
                await websocket_manager.add_ice_candidate(connection_id, candidate)
                logger.debug(f"Received ICE candidate from {connection_id}")
            
            elif msg_type == "get_room_info":
                connections = await websocket_manager.get_room_connections(stream_id)
                await websocket.send_json({
                    "type": "room_info",
                    "stream_id": stream_id,
                    "connections": len(connections)
                })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        await websocket_manager.remove_connection(connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.remove_connection(connection_id)


@router.get("/streams/{stream_id}/connections")
async def get_room_connections(stream_id: str) -> Dict[str, Any]:
    """Get all connections for a stream."""
    connections = await websocket_manager.get_room_connections(stream_id)
    
    return {
        "stream_id": stream_id,
        "connection_count": len(connections),
        "connections": connections
    }


