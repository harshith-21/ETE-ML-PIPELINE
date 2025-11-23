#!/bin/bash

# =============================================================================
# Push Custom Airflow Image to Docker Hub
# =============================================================================

set -e

IMAGE_NAME="harshith21/ete-ml-pipeline-airflow"
VERSION="2.10.1"
LATEST_TAG="latest"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Pushing Custom Airflow Image to Docker Hub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if logged in
echo "🔐 Checking Docker Hub login..."
if ! docker info | grep -q "Username"; then
    echo "Please login to Docker Hub first:"
    docker login
fi

echo ""
echo "📤 Pushing ${IMAGE_NAME}:${VERSION}..."
docker push ${IMAGE_NAME}:${VERSION}

echo ""
echo "📤 Pushing ${IMAGE_NAME}:${LATEST_TAG}..."
docker push ${IMAGE_NAME}:${LATEST_TAG}

echo ""
echo "✅ Push completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Image available at:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  https://hub.docker.com/r/${IMAGE_NAME}"
echo ""
echo "  docker pull ${IMAGE_NAME}:${VERSION}"
echo "  docker pull ${IMAGE_NAME}:${LATEST_TAG}"
echo ""

