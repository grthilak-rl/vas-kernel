"""
Phase 4.1 – AI Model IPC & Inference Contract
AI MODEL CONTAINER ORCHESTRATION

This module provides the main entry point for AI model containers.

PHASE 4.1 SCOPE:
- Container lifecycle management
- IPC server orchestration
- Graceful shutdown handling
- Signal handling for production use

WHAT THIS IS:
- Container process wrapper
- IPC server lifecycle coordinator
- Signal handler for clean shutdown

WHAT THIS IS NOT:
- Model onboarding logic (Phase 4.2)
- GPU resource management (Phase 4.2)
- Container discovery (Phase 4.2)
- Health monitoring (Phase 4.2)
- Multi-model management (one container = one model)

CONTAINER CARDINALITY (CRITICAL):
- Exactly ONE container per model type
- Containers are NOT per camera
- Containers are long-lived and pre-loaded
- Containers serve multiple cameras concurrently
"""

import signal
import sys
import time
from typing import Optional

from .inference_handler import InferenceHandler
from .ipc_server import IPCServer


class ModelContainer:
    """
    AI Model Container - long-lived inference runtime.

    ARCHITECTURE:
    - One container per model type (NOT per camera)
    - Container loads model once at startup
    - Container serves inference requests from multiple cameras
    - Container runs until explicitly stopped

    LIFECYCLE:
    1. Container starts
    2. Model loads into GPU memory (Phase 4.2: currently mock)
    3. IPC server starts listening
    4. Container processes requests indefinitely
    5. Container stops on signal (SIGTERM/SIGINT)
    6. Model unloads, IPC server stops

    CONCURRENCY:
    - Container handles concurrent requests from multiple cameras
    - Each request is independent (stateless)
    - No shared mutable state between requests
    - Thread-safe inference handler

    FAILURE ISOLATION:
    - Container failure affects ONLY this model
    - Other models continue to operate
    - Ruth AI Core detects container failure via IPC timeout
    - Container restart is external responsibility (Phase 4.2)
    """

    def __init__(self, model_id: str, model_config: Optional[dict] = None):
        """
        Initialize AI model container.

        Args:
            model_id: Unique identifier for this model
            model_config: Optional model configuration

        Example:
            container = ModelContainer(
                model_id="yolov8n",
                model_config={"device": "cuda:0", "batch_size": 1}
            )
        """
        self.model_id = model_id
        self.model_config = model_config or {}

        # Initialize inference handler (loads model in Phase 4.2)
        self.inference_handler = InferenceHandler(
            model_id=self.model_id,
            model_config=self.model_config
        )

        # Initialize IPC server
        self.ipc_server = IPCServer(
            model_id=self.model_id,
            inference_handler=self.inference_handler
        )

        # Container state
        self._running = False

    def start(self) -> None:
        """
        Start the model container.

        This method:
        1. Starts IPC server
        2. Registers signal handlers for graceful shutdown
        3. Runs until stopped

        This is a BLOCKING call. Container runs in foreground.
        """
        print(f"Starting model container: {self.model_id}")
        print(f"Model config: {self.model_config}")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        try:
            # Start IPC server
            self.ipc_server.start()
            self._running = True

            print(f"Model container {self.model_id!r} is ready to serve requests")
            print("Press Ctrl+C to stop")

            # Run indefinitely until stopped
            while self._running:
                time.sleep(1)

        except Exception as e:
            print(f"Error in model container {self.model_id!r}: {e}", file=sys.stderr)
            raise

        finally:
            # Cleanup on exit
            self._cleanup()

    def stop(self) -> None:
        """
        Stop the model container.

        This method:
        1. Stops IPC server (no new requests accepted)
        2. Waits for in-flight requests to complete
        3. Unloads model (Phase 4.2)
        4. Exits gracefully
        """
        if not self._running:
            return

        print(f"Stopping model container: {self.model_id}")
        self._running = False

    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle termination signals (SIGTERM, SIGINT).

        This enables graceful shutdown when container is stopped.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        print(f"\nReceived {signal_name}, shutting down gracefully...")
        self.stop()

    def _cleanup(self) -> None:
        """
        Clean up container resources.

        This is called during shutdown to ensure clean exit.
        """
        print(f"Cleaning up model container: {self.model_id}")

        # Stop IPC server
        self.ipc_server.stop()

        # Cleanup inference handler (unload model in Phase 4.2)
        self.inference_handler.cleanup()

        print(f"Model container {self.model_id!r} stopped")


# EXAMPLE USAGE (for testing and documentation):
#
# if __name__ == "__main__":
#     # Example: YOLOv8 object detection container
#     container = ModelContainer(
#         model_id="yolov8n",
#         model_config={
#             "device": "cuda:0",
#             "confidence_threshold": 0.5,
#             "nms_iou_threshold": 0.45
#         }
#     )
#
#     # Start container (blocks until stopped)
#     container.start()
