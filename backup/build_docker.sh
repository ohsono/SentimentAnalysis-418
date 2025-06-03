#!/bin/bash
set -e  # Exit on error

# Repository name
repo="ohsonoresearch"
image_name="ucla-sentiment-analysis"
tag="latest"

# Pull the latest base image
echo "Pulling latest base image..."
docker pull python:3.12-slim

# Create and use a new builder instance
echo "Setting up buildx..."
docker buildx create --use

# Build and push the image for both amd64 and arm64 platforms
echo "Building and pushing image..."
docker buildx build --platform linux/amd64,linux/arm64 \
    --tag docker.io/${repo}/${image_name}:${tag} \
    --push .

echo "Image successfully built and pushed to docker.io/${repo}/${image_name}:${tag}"
