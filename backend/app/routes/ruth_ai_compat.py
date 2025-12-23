"""
Ruth-AI Compatibility API endpoints.

These endpoints provide compatibility with the old VAS API that Ruth-AI currently uses.
The main differences:
- Old VAS used JWT authentication; new VAS-MS uses API keys
- Old VAS used peer-to-peer WebRTC; new VAS-MS uses MediaSoup SFU
- Old VAS had different endpoint naming conventions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel

from database import get_db
from app.models import Device
from loguru import logger

router = APIRouter(prefix="/api", tags=["Ruth-AI Compatibility"])


class WebRTCStreamRequest(BaseModel):
    """Request model for WebRTC stream (old VAS API format)."""
    device_id: str
    offer: Optional[Dict[str, Any]] = None  # SDP offer from client


class WebRTCStreamResponse(BaseModel):
    """Response model for WebRTC stream."""
    stream_id: str
    room_id: str
    websocket_url: str
    mediasoup_url: str
    status: str


@router.get("/devices")
async def list_devices_compat(
    db: AsyncSession = Depends(get_db)
):
    """
    List all devices (compatible with old VAS API).

    Old endpoint: GET /api/devices
    New endpoint: GET /api/v1/devices

    This provides compatibility for Ruth-AI.
    """
    from sqlalchemy import select

    result = await db.execute(select(Device))
    devices = result.scalars().all()

    return {
        "status": "success",
        "devices": [
            {
                "id": str(device.id),
                "name": device.name,
                "description": device.description,
                "location": device.location,
                "rtsp_url": device.rtsp_url,
                "is_active": device.is_active,
                "created_at": device.created_at,
                "updated_at": device.updated_at
            }
            for device in devices
        ]
    }


@router.get("/devices/{device_id}")
async def get_device_compat(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get device details (compatible with old VAS API).

    Old endpoint: GET /api/devices/{id}
    New endpoint: GET /api/v1/devices/{id}
    """
    from sqlalchemy import select

    try:
        device_uuid = UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )

    result = await db.execute(
        select(Device).where(Device.id == device_uuid)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return {
        "status": "success",
        "device": {
            "id": str(device.id),
            "name": device.name,
            "description": device.description,
            "location": device.location,
            "rtsp_url": device.rtsp_url,
            "is_active": device.is_active,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }
    }


@router.post("/devices/{device_id}/stream")
async def start_webrtc_stream_compat(
    device_id: str,
    request: Optional[WebRTCStreamRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Start WebRTC stream for a device (compatible with old VAS API).

    Old VAS API used peer-to-peer WebRTC with SDP offer/answer exchange.
    New VAS-MS uses MediaSoup SFU architecture with a different connection flow.

    This endpoint:
    1. Starts the RTSP→MediaSoup pipeline
    2. Returns MediaSoup connection details
    3. Client should connect to MediaSoup via WebSocket at the returned URL

    The connection flow:
    1. Client calls this endpoint to start stream
    2. Client receives room_id and websocket_url
    3. Client connects to WebSocket URL
    4. Client uses MediaSoup client library to consume the stream

    Old endpoint: POST /api/devices/{id}/stream
    New endpoint: POST /api/v1/devices/{id}/start-stream (and this compatibility endpoint)
    """
    from sqlalchemy import select
    import os

    try:
        device_uuid = UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )

    # Get device
    result = await db.execute(
        select(Device).where(Device.id == device_uuid)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Start the stream using the existing endpoint logic
    from app.services.rtsp_pipeline import rtsp_pipeline
    from app.services.mediasoup_client import mediasoup_client
    import asyncio

    try:
        room_id = str(device_uuid)

        # CHECK: If stream is already active, return existing stream info instead of restarting
        # This prevents disrupting active streams when Ruth AI or VAS portal reconnects
        if room_id in rtsp_pipeline.active_streams:
            logger.info(f"Stream already active for device {device_id}, returning existing stream info (Ruth AI compat)")
            stream_info = rtsp_pipeline.active_streams[room_id]

            # Get existing producers for this room
            try:
                existing_producers = await mediasoup_client.get_producers(room_id)
                if existing_producers:
                    # Return MediaSoup connection details for existing stream
                    backend_host = os.getenv("BACKEND_HOST", "10.30.250.245:8080")
                    websocket_url = f"ws://{backend_host}/ws/mediasoup"
                    mediasoup_url = os.getenv("MEDIASOUP_URL", "ws://10.30.250.245:3001")

                    return {
                        "status": "success",
                        "stream_id": room_id,
                        "room_id": room_id,
                        "device_id": str(device_uuid),
                        "websocket_url": websocket_url,
                        "mediasoup_url": mediasoup_url,
                        "transport_id": stream_info.get("transport_id", "unknown"),
                        "producer_id": existing_producers[-1] if existing_producers else "unknown",
                        "connection_info": {
                            "type": "mediasoup",
                            "instructions": "Connect to websocket_url using mediasoup-client library",
                            "note": "Stream already running - reconnecting to existing stream"
                        },
                        "reconnect": True
                    }
            except Exception as e:
                logger.warning(f"Error getting existing producers, will restart stream: {e}")
                # If we can't get producer info, fall through to restart the stream
                await rtsp_pipeline.stop_stream(room_id)

        # Kill orphaned FFmpeg processes
        import subprocess
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"ffmpeg.*{device.rtsp_url}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            os.kill(int(pid), 15)
                            logger.info(f"Killed orphaned FFmpeg process {pid}")
                        except (ProcessLookupError, ValueError):
                            pass
                await asyncio.sleep(1.5)
        except Exception as e:
            logger.warning(f"Error cleaning up FFmpeg: {e}")

        # Create PlainRTP transport
        logger.info(f"Creating PlainRTP transport for device {device_id}")
        transport_info = await mediasoup_client.create_plain_rtp_transport(room_id)

        if not transport_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transport"
            )

        transport_id = transport_info["id"]
        video_port = transport_info["port"]

        # Capture SSRC
        logger.info(f"Capturing SSRC from RTSP source: {device.rtsp_url}")
        detected_ssrc = await rtsp_pipeline.capture_ssrc_with_temp_ffmpeg(device.rtsp_url, timeout=15.0)

        if not detected_ssrc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to capture SSRC from RTSP source"
            )

        logger.info(f"SSRC captured: {detected_ssrc}")

        # Create producer
        video_rtp_parameters = {
            "mid": "video",
            "codecs": [{
                "mimeType": "video/H264",
                "clockRate": 90000,
                "parameters": {
                    "packetization-mode": 1,
                    "profile-level-id": "42e01f"
                },
                "payloadType": 96
            }],
            "encodings": [{"ssrc": detected_ssrc}]
        }

        # Close any old producers for this room to prevent accumulation
        try:
            old_producers = await mediasoup_client.get_producers(room_id)
            if old_producers:
                logger.info(f"Found {len(old_producers)} old producer(s) for room {room_id}, cleaning up...")
                for old_producer_id in old_producers:
                    try:
                        await mediasoup_client.close_producer(old_producer_id)
                        logger.info(f"Closed old producer: {old_producer_id}")
                    except Exception as e:
                        logger.warning(f"Failed to close old producer {old_producer_id}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up old producers: {e}")

        logger.info(f"Creating producer with SSRC: {detected_ssrc}")
        video_producer = await mediasoup_client.create_producer(
            transport_id, "video", video_rtp_parameters
        )

        # Start FFmpeg
        # Both backend and MediaSoup run in host network mode
        mediasoup_host = os.getenv("MEDIASOUP_HOST", "127.0.0.1")
        stream_info = await rtsp_pipeline.start_stream(
            stream_id=room_id,
            rtsp_url=device.rtsp_url,
            mediasoup_ip=mediasoup_host,
            mediasoup_video_port=video_port,
            ssrc=detected_ssrc
        )

        if stream_info.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start stream: {stream_info.get('error')}"
            )

        # Update device
        device.is_active = True
        await db.commit()

        # Return MediaSoup connection details
        # Client should connect to the WebSocket proxy endpoint
        backend_host = os.getenv("BACKEND_HOST", "10.30.250.245:8080")
        websocket_url = f"ws://{backend_host}/ws/mediasoup"

        # For direct MediaSoup connection (alternative)
        mediasoup_url = os.getenv("MEDIASOUP_URL", "ws://10.30.250.245:3001")

        return {
            "status": "success",
            "stream_id": room_id,
            "room_id": room_id,
            "device_id": str(device_uuid),
            "websocket_url": websocket_url,  # Recommended: through backend proxy
            "mediasoup_url": mediasoup_url,  # Alternative: direct to MediaSoup
            "transport_id": transport_id,
            "producer_id": video_producer["id"],
            "connection_info": {
                "type": "mediasoup",
                "instructions": "Connect to websocket_url using mediasoup-client library",
                "note": "This is NOT a peer-to-peer WebRTC connection. Use MediaSoup client library."
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start WebRTC stream: {e}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start stream: {str(e)}"
        )


@router.delete("/devices/{device_id}/stream")
async def stop_webrtc_stream_compat(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Stop WebRTC stream for a device (compatible with old VAS API).

    Old endpoint: DELETE /api/devices/{id}/stream
    New endpoint: POST /api/v1/devices/{id}/stop-stream
    """
    from sqlalchemy import select
    from app.services.rtsp_pipeline import rtsp_pipeline

    try:
        device_uuid = UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )

    # Get device
    result = await db.execute(
        select(Device).where(Device.id == device_uuid)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Stop stream
    try:
        stopped = await rtsp_pipeline.stop_stream(str(device_uuid))

        if stopped:
            device.is_active = False
            await db.commit()

        return {
            "status": "success",
            "device_id": str(device_uuid),
            "stopped": stopped
        }
    except Exception as e:
        logger.error(f"Failed to stop stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop stream: {str(e)}"
        )


@router.get("/streams")
async def list_streams_compat():
    """
    List active streams (compatible with old VAS API).

    Old endpoint: GET /api/streams
    """
    from app.services.rtsp_pipeline import rtsp_pipeline

    active_streams = await rtsp_pipeline.list_active_streams()

    return {
        "status": "success",
        "streams": [
            {
                "stream_id": stream_id,
                "room_id": stream_id,
                "active": True
            }
            for stream_id in active_streams
        ]
    }
