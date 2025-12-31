"""
Phase 4.1 – AI Model IPC & Inference Contract
UNIX DOMAIN SOCKET SERVER

This module implements the container-side IPC server for AI model containers.

PHASE 4.1 SCOPE:
- Unix Domain Socket (UDS) server
- Length-prefixed JSON protocol
- Synchronous request/response handling
- Connection lifecycle management

WHAT THIS IS:
- IPC transport layer only
- Protocol serialization/deserialization
- Connection handling

WHAT THIS IS NOT:
- Model loading logic (Phase 4.2)
- GPU scheduling (Phase 4.2)
- Model discovery (Phase 4.2)
- Health checks (Phase 4.2)
- Retry logic (never - caller's responsibility)

CRITICAL CONSTRAINTS:
- Containers are stateless per request
- No frame storage or buffering
- No temporal context tracking
- No per-camera state
- Strictly synchronous IPC
"""

import json
import os
import socket
import struct
import threading
from pathlib import Path
from typing import Callable, Optional

from .schema import InferenceRequest, InferenceResponse


class IPCServer:
    """
    Unix Domain Socket server for AI model container IPC.

    ARCHITECTURE:
    - One persistent UDS endpoint per container
    - Listens on: /tmp/vas_model_{model_id}.sock
    - Accepts concurrent connections
    - Each connection handles one request at a time

    PROTOCOL:
    - Length-prefixed JSON messages
    - Format: [4-byte big-endian length][JSON payload]
    - Request: InferenceRequest serialized to JSON
    - Response: InferenceResponse serialized to JSON

    CONCURRENCY MODEL:
    - One thread per connection (simple, safe)
    - Container MAY choose async I/O instead (implementation detail)
    - No shared mutable state between requests

    LIFECYCLE:
    - Container starts → UDS server binds socket
    - Server accepts connections in loop
    - Per connection: read request → invoke handler → write response → close
    - Container stops → UDS server unbinds socket

    FAILURE SEMANTICS:
    - Invalid request JSON → return error response
    - Handler exception → return error response
    - Socket error → close connection (caller retries)
    - No automatic retries, no reconnection logic
    """

    def __init__(
        self,
        model_id: str,
        inference_handler: Callable[[InferenceRequest], InferenceResponse],
        socket_dir: str = "/tmp"
    ):
        """
        Initialize IPC server for an AI model container.

        Args:
            model_id: Unique identifier for this model
            inference_handler: Callback function that processes inference requests
            socket_dir: Directory for Unix socket (default: /tmp)

        The inference_handler MUST:
        - Accept InferenceRequest as input
        - Return InferenceResponse as output
        - Be thread-safe (may be called concurrently)
        - NOT maintain state between calls
        - NOT perform retries internally

        Example:
            def my_handler(request: InferenceRequest) -> InferenceResponse:
                # Stateless inference logic here
                return InferenceResponse(...)

            server = IPCServer("yolov8", my_handler)
            server.start()
        """
        if not model_id or not isinstance(model_id, str):
            raise ValueError("model_id must be a non-empty string")

        if not callable(inference_handler):
            raise ValueError("inference_handler must be callable")

        self.model_id: str = model_id
        self.inference_handler = inference_handler
        self.socket_dir: str = socket_dir

        # UDS socket path: /tmp/vas_model_{model_id}.sock
        self.socket_path: str = os.path.join(
            self.socket_dir,
            f"vas_model_{self.model_id}.sock"
        )

        # Server state
        self._server_socket: Optional[socket.socket] = None
        self._running: bool = False
        self._accept_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """
        Start the IPC server and begin accepting connections.

        This method:
        - Creates Unix Domain Socket
        - Binds to socket path
        - Starts accept loop in background thread

        Raises:
            RuntimeError: If server is already running
            OSError: If socket cannot be created or bound
        """
        if self._running:
            raise RuntimeError(f"IPC server for model {self.model_id!r} is already running")

        # Remove stale socket file if it exists
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # Create Unix Domain Socket
        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            # Bind to socket path
            self._server_socket.bind(self.socket_path)

            # Listen for connections (backlog=5 is typical)
            self._server_socket.listen(5)

            # Set socket permissions (owner read/write only)
            os.chmod(self.socket_path, 0o600)

            # Mark server as running
            self._running = True

            # Start accept loop in background thread
            self._accept_thread = threading.Thread(
                target=self._accept_loop,
                name=f"IPCServer-{self.model_id}",
                daemon=True
            )
            self._accept_thread.start()

            print(f"IPC server started for model {self.model_id!r} at {self.socket_path}")

        except Exception as e:
            # Clean up on failure
            self._server_socket.close()
            self._server_socket = None
            raise OSError(f"Failed to start IPC server: {e}") from e

    def stop(self) -> None:
        """
        Stop the IPC server and close all connections.

        This method:
        - Stops accepting new connections
        - Closes server socket
        - Removes socket file
        - Waits for accept thread to terminate

        Note: In-flight requests are NOT interrupted.
        Container should wait for all requests to complete before stopping.
        """
        if not self._running:
            return

        # Mark server as stopped (accept loop will exit)
        self._running = False

        # Close server socket (unblocks accept())
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

        # Wait for accept thread to terminate
        if self._accept_thread:
            self._accept_thread.join(timeout=5.0)
            self._accept_thread = None

        # Remove socket file
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        print(f"IPC server stopped for model {self.model_id!r}")

    def _accept_loop(self) -> None:
        """
        Accept loop: continuously accept new connections.

        This runs in a background thread and spawns a new thread
        for each accepted connection.

        CONCURRENCY:
        - One thread per connection
        - No shared mutable state between connections
        - Each connection is independent

        ERROR HANDLING:
        - Socket errors during accept → log and continue
        - Server stopped → exit loop gracefully
        """
        while self._running:
            try:
                # Accept new connection (blocks until client connects)
                client_socket, _ = self._server_socket.accept()

                # Handle connection in separate thread
                handler_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket,),
                    name=f"IPCHandler-{self.model_id}",
                    daemon=True
                )
                handler_thread.start()

            except OSError:
                # Socket closed or error during accept
                # This is expected when server is stopping
                if self._running:
                    print(f"Error accepting connection for model {self.model_id!r}")
                break

    def _handle_connection(self, client_socket: socket.socket) -> None:
        """
        Handle a single client connection.

        PROTOCOL:
        1. Read 4-byte length prefix (big-endian)
        2. Read JSON payload of specified length
        3. Deserialize to InferenceRequest
        4. Invoke inference_handler
        5. Serialize InferenceResponse to JSON
        6. Write 4-byte length prefix + JSON payload
        7. Close connection

        ERROR HANDLING:
        - Invalid length prefix → close connection
        - Invalid JSON → return error response
        - Handler exception → return error response
        - Socket error → close connection

        Args:
            client_socket: Connected client socket
        """
        try:
            # Read request
            request = self._read_request(client_socket)

            # Invoke inference handler
            try:
                response = self.inference_handler(request)
            except Exception as e:
                # Handler raised exception → return error response
                response = InferenceResponse(
                    model_id=self.model_id,
                    camera_id=request.camera_id,
                    frame_id=request.frame_metadata.get("frame_id", 0),
                    detections=[],
                    error=f"Inference failed: {str(e)}"
                )

            # Write response
            self._write_response(client_socket, response)

        except Exception as e:
            # Connection-level error (malformed request, socket error, etc.)
            print(f"Error handling connection for model {self.model_id!r}: {e}")

        finally:
            # Always close connection
            client_socket.close()

    def _read_request(self, sock: socket.socket) -> InferenceRequest:
        """
        Read InferenceRequest from socket.

        PROTOCOL:
        - First 4 bytes: message length (big-endian uint32)
        - Next N bytes: JSON payload

        Args:
            sock: Connected socket

        Returns:
            Deserialized InferenceRequest

        Raises:
            ValueError: If request is invalid
            OSError: If socket read fails
        """
        # Read 4-byte length prefix
        length_bytes = self._read_exact(sock, 4)
        message_length = struct.unpack("!I", length_bytes)[0]

        # Sanity check: reject unreasonably large messages
        MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
        if message_length > MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {message_length} bytes")

        # Read JSON payload
        json_bytes = self._read_exact(sock, message_length)
        json_str = json_bytes.decode("utf-8")

        # Deserialize JSON to dict
        request_dict = json.loads(json_str)

        # Convert dict to InferenceRequest
        return InferenceRequest(
            frame_reference=request_dict["frame_reference"],
            frame_metadata=request_dict["frame_metadata"],
            camera_id=request_dict["camera_id"],
            model_id=request_dict["model_id"],
            timestamp=request_dict["timestamp"],
            config=request_dict.get("config")
        )

    def _write_response(self, sock: socket.socket, response: InferenceResponse) -> None:
        """
        Write InferenceResponse to socket.

        PROTOCOL:
        - First 4 bytes: message length (big-endian uint32)
        - Next N bytes: JSON payload

        Args:
            sock: Connected socket
            response: InferenceResponse to serialize

        Raises:
            OSError: If socket write fails
        """
        # Serialize response to dict
        response_dict = {
            "model_id": response.model_id,
            "camera_id": response.camera_id,
            "frame_id": response.frame_id,
            "detections": [
                {
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                    "confidence": det.confidence,
                    "bbox": det.bbox,
                    "track_id": det.track_id
                }
                for det in response.detections
            ],
            "metadata": response.metadata,
            "error": response.error
        }

        # Serialize dict to JSON
        json_str = json.dumps(response_dict)
        json_bytes = json_str.encode("utf-8")

        # Write length prefix + JSON payload
        length_bytes = struct.pack("!I", len(json_bytes))
        sock.sendall(length_bytes + json_bytes)

    def _read_exact(self, sock: socket.socket, num_bytes: int) -> bytes:
        """
        Read exactly num_bytes from socket.

        This handles partial reads by looping until all bytes are received.

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

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "running" if self._running else "stopped"
        return f"IPCServer(model_id={self.model_id!r}, status={status}, socket={self.socket_path!r})"
