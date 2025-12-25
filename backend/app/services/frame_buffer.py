"""
Frame Ring Buffer Module

Pure in-memory frame buffer for Phase 1 - Frame Ring Buffer.
This module has NO imports from MediaSoup, FFmpeg, or AI systems.
"""
from dataclasses import dataclass
from typing import Optional, List, Tuple
import threading
import time


# Frame Geometry Contract
# These constants define the ONLY supported frame geometry for Phase 1.
# No guessing, no dynamic inference per frame.

SUPPORTED_PIXEL_FORMAT = "nv12"


class FrameGeometry:
    """
    Frame geometry definition and calculation.

    NV12 format specifics:
    - Y plane: width * height bytes
    - UV plane: (width / 2) * (height / 2) * 2 bytes = width * height / 2 bytes
    - Total: width * height * 1.5 bytes
    """

    @staticmethod
    def calculate_frame_size(width: int, height: int, pixel_format: str) -> int:
        """
        Calculate frame size in bytes.

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            pixel_format: Pixel format (must be 'nv12')

        Returns:
            Frame size in bytes

        Raises:
            ValueError: If pixel format is not supported
        """
        if pixel_format.lower() != SUPPORTED_PIXEL_FORMAT:
            raise ValueError(
                f"Unsupported pixel format: {pixel_format}. "
                f"Only {SUPPORTED_PIXEL_FORMAT} is supported."
            )

        # NV12: Y plane (width * height) + UV plane (width * height / 2)
        y_plane_size = width * height
        uv_plane_size = (width * height) // 2
        return y_plane_size + uv_plane_size

    @staticmethod
    def calculate_stride(width: int, pixel_format: str) -> int:
        """
        Calculate stride (bytes per row) for Y plane.

        Args:
            width: Frame width in pixels
            pixel_format: Pixel format (must be 'nv12')

        Returns:
            Stride in bytes

        Raises:
            ValueError: If pixel format is not supported
        """
        if pixel_format.lower() != SUPPORTED_PIXEL_FORMAT:
            raise ValueError(
                f"Unsupported pixel format: {pixel_format}. "
                f"Only {SUPPORTED_PIXEL_FORMAT} is supported."
            )

        # For NV12, Y plane stride is equal to width (no padding in our case)
        return width

    @staticmethod
    def validate_geometry(
        width: int,
        height: int,
        pixel_format: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate frame geometry.

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            pixel_format: Pixel format

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check pixel format
        if pixel_format.lower() != SUPPORTED_PIXEL_FORMAT:
            return False, f"Unsupported pixel format: {pixel_format}"

        # Check width and height
        if width <= 0 or height <= 0:
            return False, f"Invalid dimensions: {width}x{height}"

        # Check that width and height are even (required for NV12)
        if width % 2 != 0 or height % 2 != 0:
            return False, f"Width and height must be even for NV12: {width}x{height}"

        return True, None


@dataclass
class FrameSlot:
    """
    A single frame slot in the ring buffer.

    Attributes:
        frame_id: Monotonic frame identifier (per camera)
        timestamp: Frame timestamp (PTS or monotonic clock)
        camera_id: Camera/stream identifier
        width: Frame width in pixels
        height: Frame height in pixels
        pixel_format: Pixel format (NV12 only)
        stride: Number of bytes per row
        data: Raw pixel buffer (bytes)
    """
    frame_id: int
    timestamp: float
    camera_id: str
    width: int
    height: int
    pixel_format: str
    stride: int
    data: bytes


class FrameRingBuffer:
    """
    Fixed-size ring buffer for decoded video frames.

    Design:
    - One buffer per camera
    - Fixed size (configurable)
    - Overwrite oldest frame when full
    - Single writer (decode thread)
    - Multiple readers (best-effort)
    - No blocking in writer path
    - No locks in writer path (single writer assumption)

    Frame loss is acceptable. Video disruption is not.
    """

    def __init__(self, camera_id: str, capacity: int = 30):
        """
        Initialize frame ring buffer.

        Args:
            camera_id: Camera/stream identifier
            capacity: Maximum number of frames to store
        """
        self.camera_id = camera_id
        self.capacity = capacity

        # Pre-allocated slots
        self.slots: List[Optional[FrameSlot]] = [None] * capacity

        # Write position (single writer, no lock needed)
        self._write_pos = 0

        # Frame counter (monotonic)
        self._next_frame_id = 0

        # Reader lock (protects read operations only)
        self._reader_lock = threading.Lock()

        # Statistics
        self._total_frames_written = 0
        self._total_frames_dropped = 0

    def push(
        self,
        timestamp: float,
        width: int,
        height: int,
        pixel_format: str,
        stride: int,
        data: bytes
    ) -> int:
        """
        Push a frame into the buffer (non-blocking).

        This is the writer path and MUST be non-blocking.
        Single writer assumption: no lock needed.

        Args:
            timestamp: Frame timestamp
            width: Frame width
            height: Frame height
            pixel_format: Pixel format
            stride: Stride in bytes
            data: Raw pixel data

        Returns:
            Frame ID assigned to this frame
        """
        frame_id = self._next_frame_id
        self._next_frame_id += 1

        # Create frame slot
        slot = FrameSlot(
            frame_id=frame_id,
            timestamp=timestamp,
            camera_id=self.camera_id,
            width=width,
            height=height,
            pixel_format=pixel_format,
            stride=stride,
            data=data
        )

        # Write to current position (overwrite if full)
        if self.slots[self._write_pos] is not None:
            self._total_frames_dropped += 1

        self.slots[self._write_pos] = slot

        # Advance write position (wrap around)
        self._write_pos = (self._write_pos + 1) % self.capacity

        self._total_frames_written += 1

        return frame_id

    def get_latest(self) -> Optional[FrameSlot]:
        """
        Get the most recent frame (best-effort, non-blocking).

        Returns:
            Latest frame slot or None if buffer is empty
        """
        with self._reader_lock:
            # Latest frame is one position before write position
            read_pos = (self._write_pos - 1) % self.capacity
            return self.slots[read_pos]

    def get_frame(self, frame_id: int) -> Optional[FrameSlot]:
        """
        Get a specific frame by ID (best-effort).

        Args:
            frame_id: Frame ID to retrieve

        Returns:
            Frame slot or None if not found
        """
        with self._reader_lock:
            for slot in self.slots:
                if slot is not None and slot.frame_id == frame_id:
                    return slot
            return None

    def get_all_frames(self) -> List[FrameSlot]:
        """
        Get all available frames (best-effort).

        Returns:
            List of frame slots (may be empty)
        """
        with self._reader_lock:
            return [slot for slot in self.slots if slot is not None]

    def get_stats(self) -> dict:
        """
        Get buffer statistics.

        Returns:
            Dictionary with buffer stats
        """
        with self._reader_lock:
            occupied_slots = sum(1 for slot in self.slots if slot is not None)

            return {
                'camera_id': self.camera_id,
                'capacity': self.capacity,
                'occupied_slots': occupied_slots,
                'write_position': self._write_pos,
                'next_frame_id': self._next_frame_id,
                'total_frames_written': self._total_frames_written,
                'total_frames_dropped': self._total_frames_dropped
            }

    def clear(self):
        """
        Clear all frames from buffer.
        """
        with self._reader_lock:
            self.slots = [None] * self.capacity
            self._write_pos = 0
