#!/bin/bash

# =============================================================================
# Build and Push Custom Airflow Image
# =============================================================================

set -e

IMAGE_NAME="harshith21/ete-ml-pipeline-airflow"
VERSION="2.10.1"
LATEST_TAG="latest"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building Custom Airflow Image (Multi-Platform)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker buildx not found. Installing..."
    docker buildx create --use
fi

# Build multi-platform image for linux/amd64 and linux/arm64
echo "📦 Building multi-platform image: ${IMAGE_NAME}:${VERSION}"
echo "   Platforms: linux/amd64, linux/arm64"
echo ""

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:${LATEST_TAG} \
    --push \
    .

echo ""
echo "✅ Build and push completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Image Details:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Repository: ${IMAGE_NAME}"
echo "  Tags: ${VERSION}, ${LATEST_TAG}"
echo "  Platforms: linux/amd64, linux/arm64"
echo ""
echo "  Docker Hub: https://hub.docker.com/r/${IMAGE_NAME}"
echo ""
echo "  To use in Kubernetes:"
echo "    image: ${IMAGE_NAME}:${LATEST_TAG}"
echo ""

