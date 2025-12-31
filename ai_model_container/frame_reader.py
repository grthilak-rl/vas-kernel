"""
Phase 4.2.2 – Frame Access, Preprocessing & Real Inference Execution

FRAME READER MODULE

This module provides READ-ONLY access to decoded frames in shared memory.

CRITICAL CONSTRAINTS:
- Frames are READ-ONLY (no mutations to shared memory)
- Frame references MUST NOT be retained beyond request scope
- Frames are copied into container-owned memory before processing
- Bad frames result in errors (no retries)
- Shared memory may disappear at any time (graceful failure)

WHAT THIS IS:
- Shared memory reader (mmap-based)
- Frame metadata parser
- Frame copy to container memory
- Format validation

WHAT THIS IS NOT:
- Frame decoder (frames are already decoded by FFmpeg)
- Frame scheduler (handled by Ruth AI Core)
- Frame buffer (stateless, no retention)
- Frame transformer (preprocessing is separate)
"""

import mmap
import os
import struct
from typing import Optional, Tuple

import numpy as np


class FrameReader:
    """
    READ-ONLY frame reader for shared memory.

    CRITICAL RULES:
    - All operations are READ-ONLY
    - No mutations to shared memory
    - Frames copied to container-owned memory
    - No retention of frame references
    - Graceful failure on bad frames
    """

    @staticmethod
    def read_frame(
        frame_reference: str,
        frame_metadata: dict
    ) -> Optional[np.ndarray]:
        """
        Read frame from shared memory (READ-ONLY).

        This method:
        1. Opens shared memory segment (READ-ONLY)
        2. Reads frame metadata header
        3. Validates frame dimensions and format
        4. COPIES frame data to container-owned NumPy array
        5. Closes shared memory (does NOT retain reference)

        CRITICAL: Frame is COPIED, not referenced.
        Original shared memory is NEVER mutated.

        Args:
            frame_reference: Path to shared memory (e.g., "/dev/shm/vas_frames_camera_1")
            frame_metadata: Frame metadata dict from IPC request
                - width: Frame width in pixels
                - height: Frame height in pixels
                - format: Pixel format (e.g., "NV12")
                - frame_id: Frame identifier
                - timestamp: Frame timestamp

        Returns:
            NumPy array containing frame data (container-owned copy)
            None if frame read fails

        Raises:
            No exceptions raised - returns None on failure
        """
        try:
            # Extract required metadata
            width = frame_metadata.get("width")
            height = frame_metadata.get("height")
            format_str = frame_metadata.get("format", "NV12")

            # Validate metadata
            if not width or not height:
                print(f"ERROR: Missing width/height in frame metadata")
                return None

            if not isinstance(width, int) or not isinstance(height, int):
                print(f"ERROR: Invalid width/height types")
                return None

            if width <= 0 or height <= 0:
                print(f"ERROR: Invalid dimensions: {width}x{height}")
                return None

            # Validate format
            if format_str != "NV12":
                print(f"ERROR: Unsupported format: {format_str} (only NV12 supported)")
                return None

            # Check if shared memory exists
            if not os.path.exists(frame_reference):
                print(f"ERROR: Shared memory does not exist: {frame_reference}")
                return None

            # Calculate expected frame size for NV12
            # NV12 format: Y plane (width * height) + UV plane (width * height / 2)
            y_plane_size = width * height
            uv_plane_size = width * height // 2
            expected_frame_size = y_plane_size + uv_plane_size

            # Get file size
            file_size = os.path.getsize(frame_reference)

            # Open shared memory (READ-ONLY)
            # CRITICAL: O_RDONLY ensures we cannot mutate shared memory
            with open(frame_reference, 'rb') as f:
                # Memory-map the file (READ-ONLY)
                # CRITICAL: mmap.ACCESS_READ ensures read-only access
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # Read frame data
                    # CRITICAL: This COPIES data from shared memory
                    frame_bytes = mm.read(expected_frame_size)

                    # Verify we read the expected amount
                    if len(frame_bytes) != expected_frame_size:
                        print(f"ERROR: Read {len(frame_bytes)} bytes, expected {expected_frame_size}")
                        return None

                    # Convert to NumPy array (container-owned copy)
                    # CRITICAL: This is a COPY, not a view
                    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8).copy()

                    # Shared memory reference is now released
                    # mm closes when context exits
                    # f closes when context exits

            # Return container-owned copy
            # Original shared memory is NO LONGER referenced
            return frame_array

        except FileNotFoundError:
            print(f"ERROR: Frame reference not found: {frame_reference}")
            return None
        except PermissionError:
            print(f"ERROR: Permission denied accessing frame: {frame_reference}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to read frame: {e}")
            return None


class NV12Preprocessor:
    """
    NV12 format preprocessor for model inference.

    NV12 is a YUV 4:2:0 format:
    - Y plane: width x height (luminance)
    - UV plane: width x height / 2 (chrominance, interleaved U and V)

    This class converts NV12 to RGB for model inference.
    """

    @staticmethod
    def nv12_to_rgb(
        frame_data: np.ndarray,
        width: int,
        height: int
    ) -> Optional[np.ndarray]:
        """
        Convert NV12 frame to RGB.

        Args:
            frame_data: Raw NV12 frame data (1D array)
            width: Frame width
            height: Frame height

        Returns:
            RGB image as NumPy array (height, width, 3) or None on failure
        """
        try:
            # Calculate plane sizes
            y_plane_size = width * height
            uv_plane_size = width * height // 2

            # Verify frame data size
            expected_size = y_plane_size + uv_plane_size
            if len(frame_data) != expected_size:
                print(f"ERROR: Frame data size mismatch: {len(frame_data)} != {expected_size}")
                return None

            # Extract Y and UV planes
            y_plane = frame_data[:y_plane_size].reshape((height, width))
            uv_plane = frame_data[y_plane_size:].reshape((height // 2, width // 2, 2))

            # Upsample UV plane to match Y plane size
            # UV is 4:2:0, so we need to upsample 2x in both dimensions
            uv_upsampled = np.repeat(np.repeat(uv_plane, 2, axis=0), 2, axis=1)

            # Extract U and V channels
            u_plane = uv_upsampled[:, :, 0]
            v_plane = uv_upsampled[:, :, 1]

            # Convert YUV to RGB using standard coefficients
            # ITU-R BT.601 conversion matrix
            y = y_plane.astype(np.float32)
            u = u_plane.astype(np.float32) - 128
            v = v_plane.astype(np.float32) - 128

            r = y + 1.402 * v
            g = y - 0.344136 * u - 0.714136 * v
            b = y + 1.772 * u

            # Clip to valid range [0, 255]
            r = np.clip(r, 0, 255).astype(np.uint8)
            g = np.clip(g, 0, 255).astype(np.uint8)
            b = np.clip(b, 0, 255).astype(np.uint8)

            # Stack to RGB image
            rgb = np.stack([r, g, b], axis=2)

            return rgb

        except Exception as e:
            print(f"ERROR: NV12 to RGB conversion failed: {e}")
            return None

    @staticmethod
    def preprocess_for_model(
        rgb_image: np.ndarray,
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True
    ) -> Optional[np.ndarray]:
        """
        Preprocess RGB image for model inference.

        Args:
            rgb_image: RGB image (height, width, 3)
            target_size: Target size for model input (width, height)
            normalize: Whether to normalize to [0, 1]

        Returns:
            Preprocessed image ready for model inference or None on failure
        """
        try:
            # This is a simplified preprocessing
            # Real preprocessing depends on specific model requirements
            # (e.g., YOLOv8, ResNet, EfficientNet all have different needs)

            # For Phase 4.2.2, we'll do basic resize and normalization
            # Model-specific preprocessing will be in Phase 4.2.3+

            # Resize (using simple nearest-neighbor for now)
            # Production would use cv2.resize or PIL.Image.resize
            import cv2
            resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_LINEAR)

            # Normalize to [0, 1] if requested
            if normalize:
                preprocessed = resized.astype(np.float32) / 255.0
            else:
                preprocessed = resized.astype(np.float32)

            # Transpose to CHW format (channels first) for PyTorch
            # Shape: (height, width, 3) -> (3, height, width)
            preprocessed = np.transpose(preprocessed, (2, 0, 1))

            return preprocessed

        except ImportError:
            print("ERROR: OpenCV not available. Install with: pip install opencv-python")
            return None
        except Exception as e:
            print(f"ERROR: Preprocessing failed: {e}")
            return None


# EXAMPLE USAGE:
#
# # Read frame from shared memory
# reader = FrameReader()
# frame_data = reader.read_frame(
#     frame_reference="/dev/shm/vas_frames_camera_1",
#     frame_metadata={"width": 1920, "height": 1080, "format": "NV12"}
# )
#
# if frame_data is not None:
#     # Convert NV12 to RGB
#     preprocessor = NV12Preprocessor()
#     rgb_image = preprocessor.nv12_to_rgb(frame_data, 1920, 1080)
#
#     if rgb_image is not None:
#         # Preprocess for model
#         model_input = preprocessor.preprocess_for_model(rgb_image, target_size=(640, 640))
#
#         if model_input is not None:
#             # Ready for inference
#             print(f"Model input shape: {model_input.shape}")
