#!/bin/bash

# =============================================================================
# Build Custom Airflow Image for LOCAL USE ONLY (Current Platform)
# =============================================================================

set -e

IMAGE_NAME="harshith21/ete-ml-pipeline-airflow"
VERSION="2.10.1"
LATEST_TAG="latest"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building Custom Airflow Image (Local Platform Only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  This builds ONLY for your current platform (macOS/Linux)"
echo "⚠️  Use ./build.sh for multi-platform builds for deployment"
echo ""

# Build the image for current platform only
echo "📦 Building image: ${IMAGE_NAME}:${VERSION}"
docker build -t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:${LATEST_TAG} .

echo ""
echo "✅ Local build completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To test locally:"
echo "  docker run -it --rm ${IMAGE_NAME}:${LATEST_TAG} bash"
echo ""
echo "To push to Docker Hub (manual):"
echo "  docker login"
echo "  docker push ${IMAGE_NAME}:${VERSION}"
echo "  docker push ${IMAGE_NAME}:${LATEST_TAG}"
echo ""
echo "⚠️  WARNING: This image may not work on Linux if built on macOS!"
echo "   For production, use: ./build.sh (multi-platform)"
echo ""

