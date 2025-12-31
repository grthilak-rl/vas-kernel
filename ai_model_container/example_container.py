#!/usr/bin/env python3
"""
Phase 4.1 – AI Model IPC & Inference Contract
EXAMPLE CONTAINER IMPLEMENTATION

This is a runnable example demonstrating the Phase 4.1 IPC contract.

USAGE:
    python3 -m ai_model_container.example_container

This will:
1. Start a model container for "yolov8n"
2. Listen on /tmp/vas_model_yolov8n.sock
3. Accept inference requests
4. Return mock detections (Phase 4.1: no real model loaded)
5. Run until Ctrl+C

TESTING:
    You can test this with a simple client:

    python3 << 'EOF'
    import json
    import socket
    import struct
    import time

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect("/tmp/vas_model_yolov8n.sock")

    request = {
        "frame_reference": "/dev/shm/vas_frames_camera_1",
        "frame_metadata": {
            "frame_id": 42,
            "width": 1920,
            "height": 1080,
            "format": "NV12",
            "timestamp": time.time()
        },
        "camera_id": "camera_1",
        "model_id": "yolov8n",
        "timestamp": time.time()
    }

    # Send request
    json_bytes = json.dumps(request).encode("utf-8")
    length = struct.pack("!I", len(json_bytes))
    sock.sendall(length + json_bytes)

    # Read response
    length_bytes = sock.recv(4)
    response_length = struct.unpack("!I", length_bytes)[0]
    response_bytes = sock.recv(response_length)
    response = json.loads(response_bytes.decode("utf-8"))

    print("Response:", json.dumps(response, indent=2))
    sock.close()
    EOF
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_model_container.container import ModelContainer


def main():
    """
    Run example AI model container.

    This demonstrates:
    - Container startup
    - IPC server initialization
    - Request handling
    - Graceful shutdown
    """

    print("=" * 80)
    print("Phase 4.1 – AI Model Container Example")
    print("=" * 80)
    print()
    print("This is a MOCK container for demonstration purposes.")
    print("No real model is loaded. Inference returns stub detections.")
    print()
    print("Phase 4.2 will add real model loading and GPU inference.")
    print()
    print("=" * 80)
    print()

    # Example: YOLOv8 Nano object detection model
    container = ModelContainer(
        model_id="yolov8n",
        model_config={
            # Phase 4.2: These will be used for real model loading
            "model_type": "yolov8",
            "variant": "nano",
            "device": "cuda:0",  # GPU device (Phase 4.2)
            "confidence_threshold": 0.5,
            "nms_iou_threshold": 0.45,
            "input_size": [640, 640],
            "classes": [
                "person", "bicycle", "car", "motorcycle", "airplane",
                "bus", "train", "truck", "boat", "traffic light"
                # ... (80 COCO classes total)
            ]
        }
    )

    print("Starting container...")
    print()

    try:
        # Start container (blocks until stopped)
        container.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Container error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
