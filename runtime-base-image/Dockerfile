# Phase 4.4 - Ruth AI Model Runtime Base Image
#
# This is the base image for ALL Ruth AI model containers.
# It provides the IPC infrastructure and common runtime dependencies.
#
# USAGE:
#   FROM ruth-ai/model-runtime:0.1.0
#
# PROVIDES:
#   - ai_model_container package (IPC server, schema, frame reader)
#   - Python 3.9 runtime
#   - NumPy, OpenCV, PyYAML
#   - Unix Domain Socket support
#   - Shared memory access (/dev/shm)
#
# MODEL CONTAINERS MUST:
#   - Extend this image
#   - Install model-specific dependencies
#   - Copy model weights
#   - Define entrypoint

FROM python:3.9-slim

LABEL maintainer="VAS AI Platform"
LABEL version="0.1.0"
LABEL description="Ruth AI Model Runtime Base Image"

# Phase 4.4: Runtime base image for AI model containers
# DO NOT modify this without explicit Phase 4.4 authorization

# Set working directory for package installation
WORKDIR /tmp/build

# Copy package files
COPY ai_model_container/ /tmp/build/ai_model_container/
COPY setup.py /tmp/build/

# Install system dependencies required by OpenCV
# Keep image minimal - only install what's absolutely needed
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install ai_model_container package and dependencies
# This installs: numpy, opencv-python-headless, PyYAML
RUN pip install --no-cache-dir .

# Clean up build artifacts
RUN rm -rf /tmp/build

# Create directories for runtime
# /dev/shm is mounted at runtime for frame access
# /tmp is used for Unix Domain Sockets
RUN mkdir -p /tmp /app

# Set default working directory for model containers
WORKDIR /app

# Runtime environment
# Model containers should override CMD with their own entrypoint
CMD ["python3", "-c", "print('Ruth AI Model Runtime v0.1.0 - Base image only, do not run directly')"]

# Fail fast if this base image is run directly
# Model containers MUST override the entrypoint
HEALTHCHECK NONE
