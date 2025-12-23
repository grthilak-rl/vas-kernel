"""
Recording Service

Handles video recording, HLS generation, and storage management.
"""
import os
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from loguru import logger


class RecordingService:
    """
    Recording Service for managing video recordings.
    
    Features:
    - HLS recording with segmented .ts files
    - Segment rotation and retention
    - Bookmark creation (±5 seconds)
    - Snapshot capture
    - Storage abstraction (local/cloud)
    """
    
    def __init__(self):
        """Initialize Recording Service."""
        self.active_recordings: Dict[str, Any] = {}
        self.hls_segment_duration = 10  # 10 seconds per segment
        self.retention_days = 7
        
        logger.info("Recording Service initialized")
    
    async def start_recording(
        self,
        stream_id: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Start HLS recording for a stream.
        
        Args:
            stream_id: Stream identifier
            output_path: Path to save recordings
            
        Returns:
            Recording configuration
        """
        if stream_id in self.active_recordings:
            logger.warning(f"Recording {stream_id} already exists")
            return self.active_recordings[stream_id]
        
        recording = {
            "stream_id": stream_id,
            "output_path": output_path,
            "started_at": datetime.now(),
            "status": "active",
            "segments": [],
            "bookmarks": [],
            "snapshots": []
        }
        
        self.active_recordings[stream_id] = recording
        logger.info(f"Started recording for stream: {stream_id}")
        
        return recording
    
    async def stop_recording(self, stream_id: str) -> bool:
        """
        Stop recording for a stream.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            True if stopped successfully
        """
        if stream_id not in self.active_recordings:
            logger.warning(f"Recording {stream_id} is not active")
            return False
        
        recording = self.active_recordings[stream_id]
        recording["status"] = "stopped"
        recording["stopped_at"] = datetime.now()
        
        # In real implementation, would:
        # - Stop FFmpeg process
        # - Finalize HLS playlist
        # - Update database
        
        del self.active_recordings[stream_id]
        logger.info(f"Stopped recording for stream: {stream_id}")
        
        return True
    
    async def add_segment(
        self,
        stream_id: str,
        segment_path: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Add a new HLS segment.
        
        Args:
            stream_id: Stream identifier
            segment_path: Path to segment file
            timestamp: Segment timestamp
            
        Returns:
            Segment information
        """
        if stream_id not in self.active_recordings:
            logger.warning(f"Recording {stream_id} not found")
            return {}
        
        segment = {
            "path": segment_path,
            "timestamp": timestamp,
            "duration": self.hls_segment_duration
        }
        
        recording = self.active_recordings[stream_id]
        recording["segments"].append(segment)
        
        logger.info(f"Added segment for stream {stream_id}: {segment_path}")
        
        return segment
    
    async def create_bookmark(
        self,
        stream_id: str,
        name: str,
        timestamp: datetime,
        duration_seconds: int = 10
    ) -> Dict[str, Any]:
        """
        Create a bookmark (±5 seconds around a timestamp).
        
        Args:
            stream_id: Stream identifier
            name: Bookmark name
            timestamp: Bookmark timestamp
            duration_seconds: Total duration (default 10 for ±5 seconds)
            
        Returns:
            Bookmark information
        """
        if stream_id not in self.active_recordings:
            logger.warning(f"Recording {stream_id} not found")
            return {}
        
        bookmark = {
            "name": name,
            "timestamp": timestamp,
            "duration": duration_seconds,
            "created_at": datetime.now(),
            "clip_url": f"/recordings/{stream_id}/bookmarks/{name}.mp4"
        }
        
        recording = self.active_recordings[stream_id]
        recording["bookmarks"].append(bookmark)
        
        logger.info(f"Created bookmark for stream {stream_id}: {name}")
        
        return bookmark
    
    async def capture_snapshot(
        self,
        stream_id: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Capture a snapshot from the stream.
        
        Args:
            stream_id: Stream identifier
            timestamp: Snapshot timestamp
            
        Returns:
            Snapshot information
        """
        snapshot = {
            "stream_id": stream_id,
            "timestamp": timestamp,
            "file_path": f"/snapshots/{stream_id}/{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg",
            "format": "jpg"
        }
        
        # Add to recording if active
        if stream_id in self.active_recordings:
            recording = self.active_recordings[stream_id]
            recording["snapshots"].append(snapshot)
        
        logger.info(f"Captured snapshot for stream {stream_id}")
        
        return snapshot
    
    async def clean_old_segments(
        self,
        stream_id: str,
        retention_days: Optional[int] = None
    ) -> int:
        """
        Clean up old segments based on retention policy.
        
        Args:
            stream_id: Stream identifier
            retention_days: Retention period in days
            
        Returns:
            Number of segments deleted
        """
        retention_days = retention_days or self.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        if stream_id not in self.active_recordings:
            return 0
        
        recording = self.active_recordings[stream_id]
        original_count = len(recording["segments"])
        
        # Filter out old segments
        recording["segments"] = [
            seg for seg in recording["segments"]
            if seg["timestamp"] > cutoff_date
        ]
        
        deleted_count = original_count - len(recording["segments"])
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old segments for stream {stream_id}")
        
        return deleted_count
    
    async def get_recording_info(self, stream_id: str) -> Dict[str, Any]:
        """
        Get information about a recording.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Recording information
        """
        if stream_id not in self.active_recordings:
            return {}
        
        recording = self.active_recordings[stream_id]
        
        return {
            "stream_id": stream_id,
            "status": recording["status"],
            "started_at": recording["started_at"],
            "segment_count": len(recording["segments"]),
            "bookmark_count": len(recording["bookmarks"]),
            "snapshot_count": len(recording["snapshots"])
        }
    
    async def list_active_recordings(self) -> List[str]:
        """
        List all active recording stream IDs.
        
        Returns:
            List of stream IDs
        """
        return list(self.active_recordings.keys())


# Global recording service instance
recording_service = RecordingService()


