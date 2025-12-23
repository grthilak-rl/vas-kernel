"""
Recording management API routes.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.recording_service import recording_service
from loguru import logger
import os

router = APIRouter(prefix="/api/v1/recordings", tags=["recordings"])


@router.post("/streams/{stream_id}/start")
async def start_recording(
    stream_id: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Start HLS recording for a stream."""
    try:
        output_path = output_path or f"/recordings/{stream_id}"
        recording = await recording_service.start_recording(stream_id, output_path)
        return {"status": "success", "recording": recording}
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/streams/{stream_id}/stop")
async def stop_recording(stream_id: str) -> Dict[str, Any]:
    """Stop recording for a stream."""
    try:
        stopped = await recording_service.stop_recording(stream_id)
        if not stopped:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        return {"status": "success", "message": f"Recording {stream_id} stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/streams/{stream_id}")
async def get_recording_info(stream_id: str) -> Dict[str, Any]:
    """Get recording information."""
    info = await recording_service.get_recording_info(stream_id)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    return info


@router.get("/streams/{stream_id}/bookmarks")
async def get_bookmarks(stream_id: str) -> Dict[str, Any]:
    """Get bookmarks for a stream."""
    info = await recording_service.get_recording_info(stream_id)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    recording = recording_service.active_recordings.get(stream_id)
    bookmarks = recording.get("bookmarks", []) if recording else []
    
    return {"status": "success", "bookmarks": bookmarks}


@router.post("/streams/{stream_id}/bookmarks")
async def create_bookmark(
    stream_id: str,
    name: str,
    timestamp: str
) -> Dict[str, Any]:
    """Create a bookmark for a stream."""
    try:
        # Parse timestamp
        ts = datetime.fromisoformat(timestamp)
        
        bookmark = await recording_service.create_bookmark(stream_id, name, ts)
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stream not being recorded"
            )
        
        return {"status": "success", "bookmark": bookmark}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/streams/{stream_id}/snapshot")
async def capture_snapshot(stream_id: str) -> Dict[str, Any]:
    """Capture a snapshot from a stream."""
    try:
        snapshot = await recording_service.capture_snapshot(stream_id, datetime.now())
        
        return {"status": "success", "snapshot": snapshot}
    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/streams/{stream_id}/cleanup")
async def cleanup_segments(
    stream_id: str,
    retention_days: Optional[int] = None
) -> Dict[str, Any]:
    """Clean up old segments."""
    try:
        deleted_count = await recording_service.clean_old_segments(
            stream_id, retention_days
        )
        
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} old segments"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup segments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/streams")
async def list_active_recordings() -> Dict[str, Any]:
    """List all active recordings."""
    streams = await recording_service.list_active_recordings()
    return {"status": "success", "active_recordings": streams}


@router.get("/devices/{device_id}/dates")
async def get_recording_dates(device_id: str) -> Dict[str, Any]:
    """Get list of dates with available recordings for a device."""
    try:
        recording_path = f"/recordings/hot/{device_id}"

        if not os.path.exists(recording_path):
            return {"status": "success", "dates": []}

        dates = []
        for item in os.listdir(recording_path):
            item_path = os.path.join(recording_path, item)
            if os.path.isdir(item_path) and len(item) == 8:  # YYYYMMDD format
                try:
                    # Validate date format
                    date_obj = datetime.strptime(item, "%Y%m%d")
                    dates.append({
                        "date": item,
                        "formatted": date_obj.strftime("%Y-%m-%d"),
                        "segments_count": len([f for f in os.listdir(item_path) if f.endswith('.ts')])
                    })
                except ValueError:
                    continue

        # Sort by date descending (newest first)
        dates.sort(key=lambda x: x["date"], reverse=True)

        return {"status": "success", "device_id": device_id, "dates": dates}

    except Exception as e:
        logger.error(f"Failed to get recording dates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/devices/{device_id}/playlist")
async def get_device_playlist(
    device_id: str,
    date: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Response:
    """
    Get HLS playlist for a device's recordings with proper VOD tags.

    Parameters:
    - device_id: Device UUID
    - date: Optional date in YYYYMMDD format (e.g., "20241201")
    - start_time: Optional start time in HH:MM:SS format (e.g., "10:00:00")
    - end_time: Optional end time in HH:MM:SS format (e.g., "12:00:00")

    If no date is provided, returns the rolling 1-hour buffer.
    If date is provided without time range, returns full day.
    If time range is provided, filters segments within that range.
    """
    try:
        # If no date specified, serve the rolling live buffer
        if not date:
            return await _serve_live_buffer_playlist(device_id)

        # Serve historical recordings for specific date/time range
        return await _serve_historical_playlist(device_id, date, start_time, end_time)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve playlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _serve_live_buffer_playlist(device_id: str) -> Response:
    """Serve the rolling 24-hour buffer playlist as EVENT (seekable but still updating)."""
    playlist_path = f"/recordings/hot/{device_id}/stream.m3u8"

    if not os.path.exists(playlist_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recordings found for this device"
        )

    # Read the original playlist generated by FFmpeg
    with open(playlist_path, 'r') as f:
        original_content = f.read()

    # Convert to EVENT playlist (seekable but continuously updating)
    lines = original_content.strip().split('\n')
    event_lines = []

    # Process each line and add EVENT tag
    for i, line in enumerate(lines):
        # Skip any existing ENDLIST tags from FFmpeg (we want continuous playback)
        if line.startswith('#EXT-X-ENDLIST'):
            continue

        event_lines.append(line)

        # Add EVENT tag right after #EXTM3U header
        if i == 0 and line.startswith('#EXTM3U'):
            event_lines.append('#EXT-X-PLAYLIST-TYPE:EVENT')

    # Do NOT add ENDLIST tag - this signals the playlist is still growing
    event_content = '\n'.join(event_lines)

    logger.info(f"Serving live buffer playlist (EVENT) for device {device_id} ({len(lines)} lines)")

    return Response(
        content=event_content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Access-Control-Allow-Origin": "*"
        }
    )


async def _serve_historical_playlist(
    device_id: str,
    date: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Response:
    """Generate VOD playlist from archived segments for specific date/time range."""

    # Validate date format
    try:
        date_obj = datetime.strptime(date, "%Y%m%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYYMMDD (e.g., 20241201)"
        )

    # Check if date directory exists
    date_path = f"/recordings/hot/{device_id}/{date}"
    if not os.path.exists(date_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recordings found for device {device_id} on {date}"
        )

    # Get all segment files
    segment_files = [f for f in os.listdir(date_path) if f.endswith('.ts') and f.startswith('segment-')]

    if not segment_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No segments found for {date}"
        )

    # Parse segment timestamps and filter by time range
    segments = []
    for filename in segment_files:
        try:
            # Extract Unix timestamp from filename (segment-1764587233.ts)
            timestamp = int(filename.split('-')[1].split('.')[0])
            segment_time = datetime.fromtimestamp(timestamp)

            # Check if segment is within requested time range
            if start_time or end_time:
                segment_time_str = segment_time.strftime("%H:%M:%S")

                if start_time and segment_time_str < start_time:
                    continue
                if end_time and segment_time_str > end_time:
                    continue

            segments.append({
                'filename': filename,
                'timestamp': timestamp,
                'time': segment_time
            })
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping invalid segment filename: {filename}")
            continue

    if not segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No segments found in specified time range"
        )

    # Sort segments by timestamp
    segments.sort(key=lambda x: x['timestamp'])

    # Generate HLS playlist
    playlist_lines = [
        '#EXTM3U',
        '#EXT-X-VERSION:3',
        '#EXT-X-PLAYLIST-TYPE:VOD',
        '#EXT-X-TARGETDURATION:6',
        f'#EXT-X-MEDIA-SEQUENCE:{segments[0]["timestamp"]}'
    ]

    # Add segments
    for segment in segments:
        playlist_lines.append('#EXTINF:6.000000,')
        # Use the full API path for segments
        segment_url = f"http://10.30.250.245:8080/api/v1/recordings/devices/{device_id}/segment-{segment['timestamp']}.ts"
        playlist_lines.append(segment_url)

    # End playlist
    playlist_lines.append('#EXT-X-ENDLIST')

    playlist_content = '\n'.join(playlist_lines)

    logger.info(
        f"Serving historical playlist for device {device_id}, "
        f"date={date}, start={start_time}, end={end_time}, "
        f"segments={len(segments)}"
    )

    return Response(
        content=playlist_content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/devices/{device_id}/{segment_name}")
async def get_segment(device_id: str, segment_name: str) -> FileResponse:
    """Get a specific recording segment (looks in today's directory)."""
    try:
        from datetime import datetime

        # Try today's date first
        today = datetime.now().strftime("%Y%m%d")
        segment_path = f"/recordings/hot/{device_id}/{today}/{segment_name}"

        # If not found in today's directory, search other dates
        if not os.path.exists(segment_path):
            device_path = f"/recordings/hot/{device_id}"
            if os.path.exists(device_path):
                # Search all date directories
                for date_dir in sorted(os.listdir(device_path), reverse=True):
                    if date_dir == "stream.m3u8":
                        continue
                    test_path = os.path.join(device_path, date_dir, segment_name)
                    if os.path.exists(test_path):
                        segment_path = test_path
                        break

        if not os.path.exists(segment_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Segment not found: {segment_name}"
            )

        return FileResponse(
            segment_path,
            media_type="video/mp2t",
            headers={"Cache-Control": "public, max-age=31536000", "Access-Control-Allow-Origin": "*"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve segment {segment_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

