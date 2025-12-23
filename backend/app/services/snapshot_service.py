"""
Snapshot service for capturing frames from live and historical streams.
"""
import os
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.snapshot import Snapshot
from app.models.device import Device


class SnapshotService:
    """Service for capturing and managing snapshots."""

    def __init__(self):
        self.snapshot_base_dir = "/snapshots"
        os.makedirs(self.snapshot_base_dir, exist_ok=True)
        logger.info(f"Snapshot service initialized. Base directory: {self.snapshot_base_dir}")

    async def capture_from_live_stream(
        self,
        device_id: str,
        rtsp_url: str,
        db: AsyncSession
    ) -> Snapshot:
        """
        Capture a snapshot from a live RTSP stream.

        Args:
            device_id: Device UUID
            rtsp_url: RTSP stream URL
            db: Database session

        Returns:
            Snapshot object with captured image
        """
        timestamp = datetime.now()
        device_dir = os.path.join(self.snapshot_base_dir, device_id)
        os.makedirs(device_dir, exist_ok=True)

        filename = f"live_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(device_dir, filename)

        logger.info(f"Capturing live snapshot from {rtsp_url} -> {file_path}")

        # FFmpeg command to capture a single frame (optimized for speed)
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-rtsp_transport", "tcp",
            "-timeout", "5000000",  # 5 second timeout for network operations (in microseconds)
            "-i", rtsp_url,
            "-frames:v", "1",  # Capture only 1 frame
            "-q:v", "2",  # High quality
            "-f", "image2",
            file_path
        ]

        try:
            # Run FFmpeg with timeout
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("FFmpeg snapshot capture timed out after 10 seconds")

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFmpeg snapshot failed: {error_msg}")
                raise RuntimeError(f"FFmpeg failed: {error_msg}")

            # Verify file was created
            if not os.path.exists(file_path):
                raise RuntimeError("Snapshot file was not created")

            file_size = os.path.getsize(file_path)
            logger.info(f"Snapshot captured successfully: {file_path} ({file_size} bytes)")

            # Create database entry
            snapshot = Snapshot(
                device_id=device_id,
                file_path=file_path,
                timestamp=timestamp,
                format="jpg",
                source="live",
                file_size=file_size
            )

            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Failed to capture live snapshot: {e}")
            # Clean up partial file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    async def capture_from_historical(
        self,
        device_id: str,
        timestamp: datetime,
        db: AsyncSession
    ) -> Snapshot:
        """
        Capture a snapshot from historical recordings.

        Args:
            device_id: Device UUID
            timestamp: Timestamp to capture from (currently just uses latest segment)
            db: Database session

        Returns:
            Snapshot object with captured image
        """
        # Find the recording segment for this timestamp
        recording_base = f"/recordings/hot/{device_id}"

        # For simplicity, use today's date (we can enhance this later to use the actual timestamp)
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        recording_date_path = os.path.join(recording_base, date_str)

        if not os.path.exists(recording_date_path):
            raise FileNotFoundError(f"No recordings found for {date_str}")

        # Get the latest segment file from the date directory
        try:
            segments = sorted([f for f in os.listdir(recording_date_path) if f.endswith('.ts')])
            if not segments:
                raise FileNotFoundError(f"No recording segments found in {date_str}")

            # Use the latest segment (or could pick one based on timestamp)
            latest_segment = segments[-1]
            segment_path = os.path.join(recording_date_path, latest_segment)

            logger.info(f"Using recording segment: {segment_path}")
        except Exception as e:
            raise FileNotFoundError(f"Failed to find recording segments: {e}")

        # Create snapshot directory
        device_dir = os.path.join(self.snapshot_base_dir, device_id)
        os.makedirs(device_dir, exist_ok=True)

        filename = f"historical_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(device_dir, filename)

        logger.info(f"Capturing historical snapshot from {segment_path} -> {file_path}")

        # FFmpeg command to extract frame from a specific segment file
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i", segment_path,
            "-frames:v", "1",
            "-q:v", "2",
            "-f", "image2",
            file_path
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("FFmpeg snapshot capture timed out after 10 seconds")

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFmpeg historical snapshot failed: {error_msg}")
                raise RuntimeError(f"FFmpeg failed: {error_msg}")

            # Verify file was created
            if not os.path.exists(file_path):
                raise RuntimeError("Snapshot file was not created")

            file_size = os.path.getsize(file_path)
            logger.info(f"Historical snapshot captured: {file_path} ({file_size} bytes)")

            # Create database entry
            snapshot = Snapshot(
                device_id=device_id,
                file_path=file_path,
                timestamp=now,  # Current time as capture time
                format="jpg",
                source="historical",
                file_size=file_size
            )

            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Failed to capture historical snapshot: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    async def list_snapshots(
        self,
        db: AsyncSession,
        device_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Snapshot]:
        """
        List snapshots, optionally filtered by device.

        Args:
            db: Database session
            device_id: Optional device ID filter
            limit: Maximum number of snapshots to return

        Returns:
            List of Snapshot objects
        """
        query = select(Snapshot)

        if device_id:
            query = query.filter(Snapshot.device_id == device_id)

        query = query.order_by(Snapshot.created_at.desc()).limit(limit)
        result = await db.execute(query)
        snapshots = result.scalars().all()
        return list(snapshots)

    async def get_snapshot(self, db: AsyncSession, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a specific snapshot by ID.

        Args:
            db: Database session
            snapshot_id: Snapshot UUID

        Returns:
            Snapshot object or None
        """
        query = select(Snapshot).filter(Snapshot.id == snapshot_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def delete_snapshot(self, db: AsyncSession, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            db: Database session
            snapshot_id: Snapshot UUID

        Returns:
            True if deleted, False if not found
        """
        snapshot = await self.get_snapshot(db, snapshot_id)
        if not snapshot:
            return False

        # Delete file
        if os.path.exists(snapshot.file_path):
            try:
                os.remove(snapshot.file_path)
                logger.info(f"Deleted snapshot file: {snapshot.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete snapshot file: {e}")

        # Delete from database
        await db.delete(snapshot)
        await db.commit()
        logger.info(f"Deleted snapshot: {snapshot_id}")

        return True


# Global instance
snapshot_service = SnapshotService()
