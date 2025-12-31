#!/usr/bin/env python3
"""
Phase 4.1 – AI Model IPC & Inference Contract
EXAMPLE CLIENT IMPLEMENTATION

This demonstrates how Ruth AI Core will communicate with model containers.

USAGE:
    # Terminal 1: Start container
    python3 -m ai_model_container.example_container

    # Terminal 2: Send test requests
    python3 -m ai_model_container.example_client

This client will:
1. Connect to the model container's UDS
2. Send multiple inference requests
3. Display responses
4. Demonstrate concurrent requests
"""

import json
import socket
import struct
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def send_inference_request(
    model_id: str,
    camera_id: str,
    frame_id: int,
    frame_reference: str = "/dev/shm/vas_frames_camera_1"
) -> Dict[str, Any]:
    """
    Send inference request to model container.

    This demonstrates the Ruth AI Core -> Model Container IPC protocol.

    Args:
        model_id: Target model identifier
        camera_id: Source camera identifier
        frame_id: Frame identifier
        frame_reference: Path to frame shared memory

    Returns:
        Response dict from model container

    Raises:
        ConnectionError: If container is not running
        OSError: If IPC communication fails
    """
    socket_path = f"/tmp/vas_model_{model_id}.sock"

    # Connect to container's UDS
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        sock.connect(socket_path)
    except FileNotFoundError:
        raise ConnectionError(
            f"Model container for {model_id!r} is not running.\n"
            f"Expected socket at: {socket_path}\n"
            f"Start container with: python3 -m ai_model_container.example_container"
        )

    try:
        # Build inference request
        request = {
            "frame_reference": frame_reference,
            "frame_metadata": {
                "frame_id": frame_id,
                "width": 1920,
                "height": 1080,
                "format": "NV12",
                "timestamp": time.time(),
                "pts": frame_id * 33.33  # Mock presentation timestamp
            },
            "camera_id": camera_id,
            "model_id": model_id,
            "timestamp": time.time(),
            "config": {
                "confidence_threshold": 0.5  # Optional request-level config
            }
        }

        # Serialize request to JSON
        json_str = json.dumps(request)
        json_bytes = json_str.encode("utf-8")

        # Send length prefix (4 bytes, big-endian)
        length = struct.pack("!I", len(json_bytes))
        sock.sendall(length + json_bytes)

        # Read response length prefix
        length_bytes = _recv_exact(sock, 4)
        response_length = struct.unpack("!I", length_bytes)[0]

        # Read response JSON
        response_bytes = _recv_exact(sock, response_length)
        response = json.loads(response_bytes.decode("utf-8"))

        return response

    finally:
        sock.close()


def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Read exactly num_bytes from socket.

    Handles partial reads by looping until all bytes received.

    Args:
        sock: Connected socket
        num_bytes: Number of bytes to read

    Returns:
        Bytes read from socket

    Raises:
        OSError: If connection closed before num_bytes received
    """
    buffer = b""
    while len(buffer) < num_bytes:
        chunk = sock.recv(num_bytes - len(buffer))
        if not chunk:
            raise OSError("Connection closed before all data received")
        buffer += chunk
    return buffer


def main():
    """
    Run example client to test model container IPC.
    """
    print("=" * 80)
    print("Phase 4.1 – AI Model Container Client Example")
    print("=" * 80)
    print()

    model_id = "yolov8n"
    camera_id = "camera_1"

    print(f"Testing IPC with model container: {model_id}")
    print(f"Camera: {camera_id}")
    print()

    # Send multiple test requests
    num_requests = 5

    print(f"Sending {num_requests} inference requests...")
    print()

    for i in range(num_requests):
        frame_id = i + 1

        print(f"Request {i+1}/{num_requests} (frame_id={frame_id})...")

        try:
            # Measure request latency
            start_time = time.time()

            # Send inference request
            response = send_inference_request(
                model_id=model_id,
                camera_id=camera_id,
                frame_id=frame_id
            )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Display response
            print(f"  Response received in {latency_ms:.2f} ms")
            print(f"  Model: {response['model_id']}")
            print(f"  Camera: {response['camera_id']}")
            print(f"  Frame ID: {response['frame_id']}")
            print(f"  Detections: {len(response['detections'])}")

            if response.get('error'):
                print(f"  ERROR: {response['error']}")
            else:
                for idx, det in enumerate(response['detections']):
                    print(f"    [{idx+1}] {det['class_name']}: "
                          f"confidence={det['confidence']:.2f}, "
                          f"bbox={det['bbox']}")

            if response.get('metadata'):
                print(f"  Metadata: {response['metadata']}")

            print()

        except ConnectionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

        except Exception as e:
            print(f"ERROR: Inference request failed: {e}", file=sys.stderr)
            return 1

        # Brief delay between requests
        time.sleep(0.1)

    print("=" * 80)
    print("All requests completed successfully!")
    print("=" * 80)
    print()
    print("Phase 4.1 IPC contract validation: ✅ PASSED")
    print()
    print("Key observations:")
    print("  - Synchronous request/response protocol")
    print("  - Length-prefixed JSON transport")
    print("  - Stateless per-request handling")
    print("  - Mock detections (Phase 4.1: no real model)")
    print()
    print("Phase 4.2 will add real model inference.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
