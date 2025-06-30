#!/bin/bash

# Build script for PE Compliance App
set -e

# Configuration
IMAGE_NAME="pe-compliance-app"
TAG="${1:-latest}"
CONTAINER_NAME="pe-compliance-app-container"

echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}"

# Build the Docker image
docker build -t "${IMAGE_NAME}:${TAG}" .

echo "✅ Docker image built successfully!"
echo ""
echo "To run the container:"
echo "  docker run -d --name ${CONTAINER_NAME} -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo ""
echo "To run with environment variables:"
echo "  docker run -d --name ${CONTAINER_NAME} -p 8000:8000 --env-file .env ${IMAGE_NAME}:${TAG}"
echo ""
echo "To stop and remove the container:"
echo "  docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME}"
echo ""
echo "To view logs:"
echo "  docker logs -f ${CONTAINER_NAME}" 