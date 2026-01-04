# Fall Detection Model Container
# Phase 4.4 - Example using Ruth AI Model Runtime Base Image
#
# This demonstrates how to build a model container on top of the base image.

FROM ruth-ai/model-runtime:0.1.0

LABEL model="fall-detection"
LABEL version="1.0.0"
LABEL description="Fall detection using pose estimation"

# Install model-specific dependencies
# PyTorch and torchvision for the fall detection model
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchvision==0.15.2

# Create model directory structure
RUN mkdir -p /app/weights /app/config

# Copy model weights (example path - adjust as needed)
# COPY weights/fall_detection_model.pt /app/weights/

# Copy model implementation
COPY fall_detection_model.py /app/

# Copy model configuration
COPY model.yaml /app/config/

# Set working directory
WORKDIR /app

# Runtime configuration
# Mount /dev/shm for frame access
# Mount /tmp for Unix Domain Sockets
VOLUME ["/dev/shm", "/tmp"]

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s = socket.socket(socket.AF_UNIX); s.connect('/tmp/vas_model_fall-detection.sock'); s.close()" || exit 1

# Start the model container
# This runs the IPC server and handles inference requests
CMD ["python3", "/app/fall_detection_model.py"]
