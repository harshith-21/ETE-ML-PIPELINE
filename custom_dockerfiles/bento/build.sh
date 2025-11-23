#!/bin/bash

set -e

IMAGE_NAME="harshith21/ete-ml-pipeline-bento"
TAG="latest"

echo "Building BentoML Docker image for ETE-ML-PIPELINE..."
echo "Image: ${IMAGE_NAME}:${TAG}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build for multiple platforms and push to Docker Hub
echo "Building multi-platform image (linux/amd64, linux/arm64)..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag ${IMAGE_NAME}:${TAG} \
    --push \
    .

echo ""
echo "✅ Build complete!"
echo "Image: ${IMAGE_NAME}:${TAG}"
echo ""
echo "The image has been pushed to Docker Hub and is ready for deployment."

