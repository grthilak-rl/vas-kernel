"""
Stream API routes for serving HLS playlists.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from typing import Dict, Any
from app.services.rtsp_pipeline import rtsp_pipeline
from loguru import logger
import os

router = APIRouter(prefix="/api/v1/streams", tags=["streams"])


@router.get("/{stream_id}/playlist.m3u8")
async def get_hls_playlist(stream_id: str) -> FileResponse:
    """Get HLS playlist for a stream."""
    # Check if stream is active
    active_streams = await rtsp_pipeline.list_active_streams()
    if stream_id not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found or not active"
        )
    
    # Serve the playlist file
    playlist_path = f"/tmp/streams/{stream_id}/stream.m3u8"
    
    if not os.path.exists(playlist_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist file not found"
        )
    
    return FileResponse(
        playlist_path,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/{stream_id}/{segment_name}")
async def get_hls_segment(stream_id: str, segment_name: str) -> FileResponse:
    """Get HLS segment file for a stream."""
    # Check if stream is active
    active_streams = await rtsp_pipeline.list_active_streams()
    if stream_id not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found or not active"
        )
    
    # Serve the segment file
    segment_path = f"/tmp/streams/{stream_id}/{segment_name}"
    
    if not os.path.exists(segment_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment file not found"
        )
    
    return FileResponse(
        segment_path,
        media_type="video/mp2t",
        headers={"Cache-Control": "no-cache"}
    )
