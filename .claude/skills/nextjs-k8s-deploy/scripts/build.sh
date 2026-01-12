#!/bin/bash
IMAGE_NAME=$1

if [ -z "$IMAGE_NAME" ]; then
  echo "Usage: ./build.sh <image_name>"
  exit 1
fi

echo "Building Docker image: $IMAGE_NAME..."

# If using minikube, we usually use the minikube docker-env
# eval $(minikube docker-env)

docker build -t "$IMAGE_NAME" .

echo "✓ Image $IMAGE_NAME built successfully."
