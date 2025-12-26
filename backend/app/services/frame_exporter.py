"""
Phase 2 - Frame Export Interface

This module provides write-only shared memory frame export for decoded video frames.

ARCHITECTURAL CONSTRAINTS (NON-NEGOTIABLE):
- VAS is the sole writer; external processes are readers
- Best-effort, pull-based semantics only
- No locks, no waits, no retries, no acknowledgements
- Local shared memory only (/dev/shm/vas/<camera_id>/)
- Zero impact when AI_FRAME_EXPORT_ENABLED=false
- Failure of readers must never affect VAS

EXPORT MECHANISM:
- frame.data: raw NV12 frame bytes
- frame.meta: fixed-size binary metadata header
- Metadata written AFTER frame data (synchronization point)
- Polling-based read by external consumers

LIFECYCLE:
- Shared memory created on camera stream start
- Shared memory removed on camera stream stop
- All operations are best-effort and non-blocking
"""

import os
import struct
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Phase 2 metadata version
METADATA_VERSION = 1

# Shared memory base path
SHM_BASE_PATH = "/dev/shm/vas"

# Fixed-size binary metadata format (64 bytes)
# Field order is FIXED per version - never change existing fields
METADATA_STRUCT = struct.Struct(
    "I"      # version (uint32) - MUST be first field
    "Q"      # frame_id (uint64)
    "Q"      # timestamp_ns (uint64)
    "I"      # width (uint32)
    "I"      # height (uint32)
    "I"      # pixel_format (uint32) - 0=NV12
    "I"      # stride (uint32)
    "Q"      # data_size (uint64)
    "16x"    # reserved (16 bytes) - for future extensions
)

# Pixel format constants
PIXEL_FORMAT_NV12 = 0


class FrameExporter:
    """
    Write-only frame exporter using shared memory.

    VAS writes frames to /dev/shm/vas/<camera_id>/ with:
    - frame.data (raw frame bytes)
    - frame.meta (fixed-size binary header)

    External processes poll frame.meta for updates and read frame.data.

    CRITICAL: This class NEVER blocks, waits, or retries.
    All failures are logged and ignored to protect VAS stability.
    """

    def __init__(self, camera_id: str):
        """
        Initialize frame exporter for a specific camera.

        Args:
            camera_id: Unique camera identifier
        """
        self.camera_id = camera_id
        self.camera_dir = Path(SHM_BASE_PATH) / camera_id
        self.frame_data_path = self.camera_dir / "frame.data"
        self.frame_meta_path = self.camera_dir / "frame.meta"
        self._initialized = False

    def initialize(self) -> bool:
        """
        Create shared memory directory structure.

        Best-effort operation. Returns success status but VAS must
        continue regardless of result.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create camera directory
            self.camera_dir.mkdir(parents=True, exist_ok=True)

            # Create empty placeholder files
            self.frame_data_path.touch(exist_ok=True)
            self.frame_meta_path.touch(exist_ok=True)

            # Set permissive permissions for local readers
            os.chmod(self.camera_dir, 0o755)
            os.chmod(self.frame_data_path, 0o644)
            os.chmod(self.frame_meta_path, 0o644)

            self._initialized = True
            logger.info(f"Frame export initialized for camera {self.camera_id} at {self.camera_dir}")
            return True

        except Exception as e:
            # CRITICAL: Never raise - log and continue
            logger.error(f"Failed to initialize frame export for camera {self.camera_id}: {e}")
            self._initialized = False
            return False

    def export_frame(
        self,
        frame_id: int,
        timestamp_ns: int,
        width: int,
        height: int,
        pixel_format: str,
        stride: int,
        data: bytes
    ) -> None:
        """
        Export a single frame to shared memory.

        Write order (CRITICAL for synchronization):
        1. Write frame.data (raw bytes)
        2. Write frame.meta (metadata header)

        Metadata write is the only synchronization mechanism.
        Readers poll frame.meta and use frame_id to detect updates.

        Args:
            frame_id: Monotonic frame identifier
            timestamp_ns: Frame timestamp in nanoseconds
            width: Frame width in pixels
            height: Frame height in pixels
            pixel_format: Pixel format string (e.g., "nv12")
            stride: Frame stride in bytes
            data: Raw frame bytes

        CRITICAL: This method NEVER blocks or raises exceptions.
        All failures are silently logged to protect VAS.
        """
        if not self._initialized:
            # Silently skip if not initialized
            return

        try:
            # Convert pixel format string to constant
            pixel_format_code = PIXEL_FORMAT_NV12  # Phase 2 only supports NV12

            data_size = len(data)

            # Step 1: Write frame data
            # Use atomic write with temp file + rename for safety
            temp_data_path = self.frame_data_path.with_suffix(".tmp")
            with open(temp_data_path, "wb") as f:
                f.write(data)
            os.replace(temp_data_path, self.frame_data_path)

            # Step 2: Pack metadata (fixed-size binary header)
            metadata_bytes = METADATA_STRUCT.pack(
                METADATA_VERSION,      # version
                frame_id,              # frame_id
                timestamp_ns,          # timestamp_ns
                width,                 # width
                height,                # height
                pixel_format_code,     # pixel_format
                stride,                # stride
                data_size              # data_size
            )

            # Step 3: Write metadata AFTER frame data
            # Metadata write is the synchronization point for readers
            temp_meta_path = self.frame_meta_path.with_suffix(".tmp")
            with open(temp_meta_path, "wb") as f:
                f.write(metadata_bytes)
            os.replace(temp_meta_path, self.frame_meta_path)

            # Success - no logging to avoid spam

        except Exception as e:
            # CRITICAL: Never raise - log and continue
            # Use warning level to avoid log spam on transient errors
            logger.warning(f"Frame export failed for camera {self.camera_id}, frame {frame_id}: {e}")

    def cleanup(self) -> None:
        """
        Remove shared memory files and directory.

        Best-effort cleanup on camera stream stop.
        Readers will naturally fail on next access.

        CRITICAL: This method NEVER blocks or raises exceptions.
        """
        if not self._initialized:
            return

        try:
            # Remove files
            if self.frame_data_path.exists():
                self.frame_data_path.unlink()

            if self.frame_meta_path.exists():
                self.frame_meta_path.unlink()

            # Remove directory
            if self.camera_dir.exists():
                self.camera_dir.rmdir()

            self._initialized = False
            logger.info(f"Frame export cleaned up for camera {self.camera_id}")

        except Exception as e:
            # CRITICAL: Never raise - log and continue
            logger.error(f"Failed to cleanup frame export for camera {self.camera_id}: {e}")
