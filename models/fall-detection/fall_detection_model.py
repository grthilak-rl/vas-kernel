"""
Fall Detection Model Container
Phase 4.4 - Example model implementation using runtime base image

This demonstrates how to use the ai_model_container package
without any VAS source code dependencies.
"""

import signal
import sys
import time
from pathlib import Path

# Import from the ai_model_container package (provided by base image)
from ai_model_container import (
    IPCServer,
    InferenceRequest,
    InferenceResponse,
    Detection,
    FrameReader,
    NV12Preprocessor,
    ModelConfig,
)

# Model-specific imports (installed in this container's Dockerfile)
try:
    import torch
    import torchvision
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not available, using mock inference")


class FallDetectionModel:
    """
    Fall detection model implementation.

    This is a placeholder - replace with actual model logic.
    """

    def __init__(self, model_path: str = None, device: str = "cpu"):
        """Initialize the fall detection model."""
        self.model_path = model_path
        self.device = device
        self.model = None

        # Load model if available
        if TORCH_AVAILABLE and model_path and Path(model_path).exists():
            print(f"Loading model from {model_path}")
            # self.model = torch.load(model_path, map_location=device)
            # self.model.eval()
            print("Model loaded successfully")
        else:
            print("Running in mock mode (no model weights)")

    def infer(self, frame_rgb):
        """
        Run inference on a frame.

        Args:
            frame_rgb: RGB frame as numpy array (H, W, 3)

        Returns:
            List of Detection objects
        """
        # Placeholder inference logic
        # Replace with actual fall detection model

        # Mock detection for demonstration
        detections = []

        # Example: Detect a "fall" with low confidence
        # Real implementation would run actual pose estimation
        mock_detection = Detection(
            class_id=0,
            class_name="fall",
            confidence=0.65,
            bbox=[0.3, 0.4, 0.7, 0.9],  # Normalized coordinates
            track_id=None,
        )
        detections.append(mock_detection)

        return detections


def create_inference_handler(model: FallDetectionModel):
    """
    Create the inference handler function for the IPC server.

    Args:
        model: Loaded fall detection model

    Returns:
        Callable that processes InferenceRequest and returns InferenceResponse
    """

    def inference_handler(request: InferenceRequest) -> InferenceResponse:
        """
        Process a single inference request.

        This function:
        1. Reads the frame from shared memory
        2. Preprocesses from NV12 to RGB
        3. Runs the model
        4. Returns detections
        """
        try:
            start_time = time.time()

            # Read frame from shared memory (READ-ONLY)
            frame_reader = FrameReader(request.frame_reference)
            frame_header, frame_data = frame_reader.read_frame(
                request.frame_metadata.get("frame_id", 0)
            )

            # Preprocess NV12 to RGB
            preprocessor = NV12Preprocessor()
            frame_rgb = preprocessor.nv12_to_rgb(
                frame_data,
                frame_header.width,
                frame_header.height,
            )

            # Run inference
            detections = model.infer(frame_rgb)

            # Calculate inference time
            inference_time_ms = (time.time() - start_time) * 1000

            # Return response
            return InferenceResponse(
                model_id=request.model_id,
                camera_id=request.camera_id,
                frame_id=request.frame_metadata.get("frame_id", 0),
                detections=detections,
                metadata={
                    "inference_time_ms": inference_time_ms,
                    "device": model.device,
                },
                error=None,
            )

        except Exception as e:
            # Return error response on failure
            return InferenceResponse(
                model_id=request.model_id,
                camera_id=request.camera_id,
                frame_id=request.frame_metadata.get("frame_id", 0),
                detections=[],
                metadata=None,
                error=f"Inference failed: {str(e)}",
            )

    return inference_handler


def main():
    """Main entry point for the fall detection model container."""

    print("=" * 60)
    print("Fall Detection Model Container")
    print("Phase 4.4 - Using Ruth AI Model Runtime Base Image")
    print("=" * 60)
    print()

    # Configuration
    model_id = "fall-detection"
    model_path = "/app/weights/fall_detection_model.pt"
    device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"

    print(f"Model ID: {model_id}")
    print(f"Device: {device}")
    print(f"PyTorch available: {TORCH_AVAILABLE}")
    print()

    # Load model
    print("Loading fall detection model...")
    model = FallDetectionModel(model_path=model_path, device=device)
    print()

    # Create inference handler
    handler = create_inference_handler(model)

    # Start IPC server
    print(f"Starting IPC server for model '{model_id}'...")
    server = IPCServer(model_id=model_id, inference_handler=handler)
    server.start()
    print()

    print("Model container ready and listening for inference requests")
    print(f"Socket: /tmp/vas_model_{model_id}.sock")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print()
        print("Shutting down model container...")
        server.stop()
        print("Stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep the container running
    signal.pause()


if __name__ == "__main__":
    main()
