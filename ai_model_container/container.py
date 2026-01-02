"""
Phase 4.1 – AI Model IPC & Inference Contract
Phase 4.2.3 – Model Onboarding & Discovery
Phase 7 – Observability & Operational Controls

AI MODEL CONTAINER ORCHESTRATION

This module provides the main entry point for AI model containers.

PHASE 4.1 SCOPE:
- Container lifecycle management
- IPC server orchestration
- Graceful shutdown handling
- Signal handling for production use

PHASE 4.2.3 ADDITIONS:
- Model discovery integration
- GPU requirement enforcement
- model.yaml-based configuration
- Fail-fast on GPU absence (when required)

PHASE 7 SCOPE:
- Heartbeat emission (periodic, best-effort)
- Per-container metrics tracking (requests, errors, latency)
- Liveness signaling for operational visibility
- Non-blocking metrics collection
- Silent failure on metrics errors

WHAT THIS IS:
- Container process wrapper
- IPC server lifecycle coordinator
- Signal handler for clean shutdown
- Model configuration validator
- Heartbeat emitter (Phase 7)

WHAT THIS IS NOT:
- Health monitoring (read-only visibility only)
- Multi-model management (one container = one model)
- Hot-reload mechanism
- Runtime configuration updates
- Alerting or auto-restart system

CONTAINER CARDINALITY (CRITICAL):
- Exactly ONE container per model type
- Containers are NOT per camera
- Containers are long-lived and pre-loaded
- Containers serve multiple cameras concurrently
"""

import json
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .inference_handler import InferenceHandler
from .ipc_server import IPCServer
from .model_config import ModelConfig
from .model_discovery import ModelDiscovery


class ModelContainer:
    """
    AI Model Container - long-lived inference runtime.

    ARCHITECTURE:
    - One container per model type (NOT per camera)
    - Container loads model once at startup
    - Container serves inference requests from multiple cameras
    - Container runs until explicitly stopped

    LIFECYCLE (Phase 4.2.3):
    1. Container starts with model_id
    2. Model discovered via filesystem scan (model.yaml)
    3. GPU requirements validated
    4. Model loads into GPU/CPU memory
    5. IPC server starts listening
    6. Container processes requests indefinitely
    7. Container stops on signal (SIGTERM/SIGINT)
    8. Model unloads, IPC server stops

    GPU REQUIREMENT ENFORCEMENT:
    - If gpu_required=true and NO GPU → container FAILS FAST
    - If cpu_fallback_allowed=true and NO GPU → container runs on CPU
    - If gpu_required=false → container runs on CPU

    CONCURRENCY:
    - Container handles concurrent requests from multiple cameras
    - Each request is independent (stateless)
    - No shared mutable state between requests
    - Thread-safe inference handler

    FAILURE ISOLATION:
    - Container failure affects ONLY this model
    - Other models continue to operate
    - Ruth AI Core detects container failure via IPC timeout
    - Container restart is external responsibility
    """

    def __init__(
        self,
        model_id: str,
        model_config: Optional[dict] = None,
        models_dir: Optional[str] = None
    ):
        """
        Initialize AI model container.

        Phase 4.2.3 Behavior:
        - Attempts to discover model via filesystem scan
        - Falls back to legacy model_config if discovery fails
        - Enforces GPU requirements from model.yaml

        Args:
            model_id: Unique identifier for this model
            model_config: Optional legacy model configuration (Phase 4.2.1/4.2.2 compat)
            models_dir: Optional models directory (default: /opt/ruth-ai/models)

        Raises:
            RuntimeError: If GPU required but unavailable
            RuntimeError: If model discovery fails and no config provided

        Example (Phase 4.2.3 - model.yaml):
            container = ModelContainer(model_id="yolov8n")

        Example (Phase 4.2.1/4.2.2 - legacy):
            container = ModelContainer(
                model_id="yolov8n",
                model_config={"device": "cuda:0", "model_type": "pytorch", "model_path": "/path/to/model.pt"}
            )
        """
        self.model_id = model_id
        self._running = False

        # Phase 7: Observability metrics (best-effort, non-blocking)
        # CRITICAL: Metrics MUST NOT affect inference or container lifecycle
        self._start_time = time.time()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_stop_event = threading.Event()

        # Phase 4.2.3: Try model discovery first
        discovered_config = None
        if models_dir is not None or model_config is None:
            # Attempt discovery
            print(f"Attempting model discovery for: {model_id}")
            discovery = ModelDiscovery(models_dir=models_dir)
            available_models = discovery.discover_models()

            if discovery.is_available(model_id):
                model_cfg = discovery.get_model(model_id)
                print(f"Model discovered: {model_cfg}")

                # CRITICAL: Enforce GPU requirements
                if model_cfg.gpu_required:
                    # Check if GPU is actually available
                    gpu_available = self._check_gpu_available()
                    if not gpu_available:
                        raise RuntimeError(
                            f"FATAL: Model {model_id!r} requires GPU (gpu_required=true) "
                            f"but no GPU is available. Container cannot start."
                        )
                    print(f"GPU required and available for model {model_id}")

                # Convert to runtime config
                discovered_config = model_cfg.to_runtime_config()
                print(f"Using discovered configuration: {discovered_config}")
            else:
                reason = discovery.get_unavailable_reason(model_id)
                print(f"WARNING: Model {model_id!r} not discovered or unavailable")
                if reason:
                    print(f"         Reason: {reason}")

        # Determine final configuration
        if discovered_config is not None:
            # Phase 4.2.3: Use discovered config
            self.model_config = discovered_config
            print(f"Container using discovered configuration for {model_id}")
        elif model_config is not None:
            # Phase 4.2.1/4.2.2: Use legacy config
            self.model_config = model_config
            print(f"Container using legacy configuration for {model_id}")
        else:
            # No config available - FAIL
            raise RuntimeError(
                f"FATAL: Model {model_id!r} could not be discovered and no legacy config provided. "
                f"Container cannot start."
            )

        # Initialize inference handler (loads model)
        self.inference_handler = InferenceHandler(
            model_id=self.model_id,
            model_config=self.model_config
        )

        # Initialize IPC server
        self.ipc_server = IPCServer(
            model_id=self.model_id,
            inference_handler=self.inference_handler
        )

    def _check_gpu_available(self) -> bool:
        """
        Check if GPU is available.

        Returns:
            True if CUDA GPU available, False otherwise
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # PyTorch not available - assume no GPU
            return False

    def start(self) -> None:
        """
        Start the model container.

        Phase 7: Also starts heartbeat emission thread.

        This method:
        1. Starts IPC server
        2. Registers signal handlers for graceful shutdown
        3. Starts heartbeat emission (Phase 7, best-effort)
        4. Runs until stopped

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

            # Phase 7: Start heartbeat emission (best-effort, non-blocking)
            # CRITICAL: Heartbeat thread MUST NOT block or affect inference
            self._start_heartbeat_thread()

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

        Phase 7: Also stops heartbeat emission.

        This is called during shutdown to ensure clean exit.
        """
        print(f"Cleaning up model container: {self.model_id}")

        # Phase 7: Stop heartbeat thread (best-effort, non-blocking)
        self._stop_heartbeat_thread()

        # Stop IPC server
        self.ipc_server.stop()

        # Cleanup inference handler (unload model in Phase 4.2)
        self.inference_handler.cleanup()

        print(f"Model container {self.model_id!r} stopped")

    def _start_heartbeat_thread(self) -> None:
        """
        Phase 7: Start background heartbeat emission thread.

        Emits periodic heartbeat to /tmp/vas_heartbeat_{model_id}.json
        containing liveness and metrics information.

        CRITICAL: This MUST be non-blocking and best-effort.
        - Heartbeat failures are silently ignored
        - Thread runs as daemon (won't prevent shutdown)
        - No retry logic
        - No alerts

        Heartbeat interval: 5 seconds (configurable via environment variable)
        """
        try:
            # Don't start if already running
            if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
                return

            self._heartbeat_stop_event.clear()
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                name=f"heartbeat-{self.model_id}",
                daemon=True  # Daemon thread won't prevent shutdown
            )
            self._heartbeat_thread.start()
            print(f"Phase 7: Heartbeat emission started for model {self.model_id}")
        except Exception as e:
            # Phase 7: Silent failure - heartbeat errors must not affect container startup
            print(f"WARNING: Failed to start heartbeat thread: {e}", file=sys.stderr)

    def _stop_heartbeat_thread(self) -> None:
        """
        Phase 7: Stop background heartbeat emission thread.

        CRITICAL: This MUST be non-blocking.
        - No wait for in-flight heartbeat
        - Signal thread to stop and return immediately
        """
        try:
            if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
                self._heartbeat_stop_event.set()
                # Don't join() - we want non-blocking shutdown
                print(f"Phase 7: Heartbeat emission stopped for model {self.model_id}")
        except Exception:
            # Phase 7: Silent failure - heartbeat cleanup errors are ignored
            pass

    def _heartbeat_loop(self) -> None:
        """
        Phase 7: Background heartbeat emission loop.

        Periodically emits heartbeat containing:
        - model_id
        - timestamp
        - status (healthy/degraded/unknown)
        - metrics (total_requests, total_errors, avg_latency_ms, uptime_seconds)

        CRITICAL: This MUST NOT raise exceptions or block container operation.
        All errors are silently handled.
        """
        # Get heartbeat interval from environment (default: 5 seconds)
        import os
        heartbeat_interval = int(os.environ.get("VAS_HEARTBEAT_INTERVAL_SECONDS", "5"))

        while not self._heartbeat_stop_event.is_set():
            try:
                self._emit_heartbeat()
            except Exception as e:
                # Phase 7: Silent failure - heartbeat errors must not propagate
                # Log to stderr for debugging but don't crash
                print(f"WARNING: Heartbeat emission failed: {e}", file=sys.stderr)

            # Sleep with interruptible wait
            self._heartbeat_stop_event.wait(timeout=heartbeat_interval)

    def _emit_heartbeat(self) -> None:
        """
        Phase 7: Emit single heartbeat to filesystem.

        Writes heartbeat JSON to /tmp/vas_heartbeat_{model_id}.json

        CRITICAL: This MUST be atomic and best-effort.
        - Write to temp file first, then rename (atomic)
        - Silent failure on errors
        - No retry logic
        """
        try:
            # Get metrics from inference handler (best-effort)
            metrics = self._get_container_metrics()

            # Build heartbeat payload
            heartbeat = {
                "model_id": self.model_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "healthy",  # Simple status for Phase 7
                "metrics": metrics
            }

            # Write to temp file first (atomic write)
            heartbeat_path = Path(f"/tmp/vas_heartbeat_{self.model_id}.json")
            temp_path = Path(f"/tmp/.vas_heartbeat_{self.model_id}.json.tmp")

            with temp_path.open("w") as f:
                json.dump(heartbeat, f, indent=2)

            # Atomic rename
            temp_path.replace(heartbeat_path)

        except Exception:
            # Phase 7: Silent failure - heartbeat write errors are ignored
            pass

    def _get_container_metrics(self) -> dict:
        """
        Phase 7: Get container-level metrics for heartbeat.

        Returns:
            Dictionary containing:
            - total_requests: Total inference requests processed
            - total_errors: Total failed inferences
            - avg_latency_ms: Average inference latency (milliseconds)
            - uptime_seconds: Container uptime

        CRITICAL: This is best-effort.
        - Missing metrics return 0 or None
        - Errors are silently handled
        """
        try:
            uptime = time.time() - self._start_time

            # Get metrics from inference handler (if available)
            handler_metrics = {}
            if hasattr(self.inference_handler, 'get_metrics'):
                try:
                    handler_metrics = self.inference_handler.get_metrics()
                except Exception:
                    pass

            # Get metrics from IPC server (if available)
            ipc_metrics = {}
            if hasattr(self.ipc_server, 'get_metrics'):
                try:
                    ipc_metrics = self.ipc_server.get_metrics()
                except Exception:
                    pass

            return {
                "total_requests": handler_metrics.get("total_requests", 0) or ipc_metrics.get("total_requests", 0),
                "total_errors": handler_metrics.get("total_errors", 0) or ipc_metrics.get("total_errors", 0),
                "avg_latency_ms": handler_metrics.get("avg_latency_ms", 0.0),
                "uptime_seconds": int(uptime)
            }
        except Exception:
            # Phase 7: Silent failure - return empty metrics
            return {
                "total_requests": 0,
                "total_errors": 0,
                "avg_latency_ms": 0.0,
                "uptime_seconds": 0
            }


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
