#!/bin/bash
# Phase 4.4 - Ruth AI Model Runtime Base Image Build Script
#
# This script builds the runtime base image for all Ruth AI model containers.
#
# USAGE:
#   ./build.sh [version]
#
# EXAMPLE:
#   ./build.sh 0.1.0

set -e

VERSION="${1:-0.1.0}"
IMAGE_NAME="ruth-ai/model-runtime"
FULL_TAG="${IMAGE_NAME}:${VERSION}"
LATEST_TAG="${IMAGE_NAME}:latest"

echo "Building Ruth AI Model Runtime Base Image"
echo "Version: ${VERSION}"
echo "Image: ${FULL_TAG}"
echo ""

# Build the image
docker build \
  --tag "${FULL_TAG}" \
  --tag "${LATEST_TAG}" \
  --build-arg VERSION="${VERSION}" \
  .

echo ""
echo "Build complete!"
echo ""
echo "Image tags:"
echo "  ${FULL_TAG}"
echo "  ${LATEST_TAG}"
echo ""
echo "To use in a model container:"
echo "  FROM ${FULL_TAG}"
echo ""
echo "To verify installation:"
echo "  docker run --rm ${FULL_TAG} python3 -c 'import ai_model_container; print(ai_model_container.__version__)'"
