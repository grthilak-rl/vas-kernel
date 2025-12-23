"""
RTSP Pipeline API routes.

Handles RTSP stream management.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.services.rtsp_pipeline import rtsp_pipeline
from loguru import logger

router = APIRouter(prefix="/api/v1/rtsp", tags=["rtsp"])


@router.post("/streams/{stream_id}/start")
async def start_rtsp_stream(
    stream_id: str,
    rtsp_url: str,
    output_port: int = None,
    output_host: str = "127.0.0.1"
) -> Dict[str, Any]:
    """Start an RTSP stream."""
    try:
        stream_info = await rtsp_pipeline.start_stream(
            stream_id, 
            rtsp_url, 
            output_port=output_port,
            output_host=output_host
        )
        return {"status": "success", "stream": stream_info}
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/streams/{stream_id}/stop")
async def stop_rtsp_stream(stream_id: str) -> Dict[str, Any]:
    """Stop an RTSP stream."""
    try:
        stopped = await rtsp_pipeline.stop_stream(stream_id)
        if not stopped:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stream not found"
            )
        return {"status": "success", "message": f"Stream {stream_id} stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/streams/{stream_id}/health")
async def check_stream_health(stream_id: str) -> Dict[str, Any]:
    """Check stream health."""
    health_status = await rtsp_pipeline.check_stream_health(stream_id)
    
    if health_status.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    return health_status


@router.get("/streams/{stream_id}/stats")
async def get_stream_stats(stream_id: str) -> Dict[str, Any]:
    """Get stream statistics."""
    stats = await rtsp_pipeline.get_stream_stats(stream_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    return stats


@router.post("/streams/{stream_id}/reconnect")
async def reconnect_stream(stream_id: str) -> Dict[str, Any]:
    """Reconnect a failed stream."""
    try:
        reconnected = await rtsp_pipeline.reconnect_stream(stream_id)
        if not reconnected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stream not found"
            )
        return {"status": "success", "message": f"Stream {stream_id} reconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reconnect stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/streams")
async def list_active_streams() -> Dict[str, Any]:
    """List all active streams."""
    streams = await rtsp_pipeline.list_active_streams()
    return {"status": "success", "active_streams": streams}


