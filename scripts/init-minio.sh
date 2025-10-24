#!/bin/bash
set -e

# MinIO bucket initialization script
# This script creates the necessary buckets for the dating app

MINIO_ENDPOINT="http://minio:9000"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:-dating}"
MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD:-dating123}"

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until curl -f "${MINIO_ENDPOINT}/minio/health/live" >/dev/null 2>&1; do
    echo "MinIO is not ready yet, waiting..."
    sleep 2
done

echo "MinIO is ready, creating buckets..."

# Install MinIO client
if ! command -v mc &> /dev/null; then
    echo "Installing MinIO client..."
    curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
    sudo mv mc /usr/local/bin/
fi

# Configure MinIO client
mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

# Create buckets
echo "Creating buckets..."

# Photos bucket
mc mb local/photos --ignore-existing
echo "Created bucket: photos"

# Thumbnails bucket  
mc mb local/thumbnails --ignore-existing
echo "Created bucket: thumbnails"

# Verification selfies bucket
mc mb local/verification --ignore-existing
echo "Created bucket: verification"

# Set bucket policies (public read for photos and thumbnails)
mc anonymous set public local/photos
mc anonymous set public local/thumbnails

echo "MinIO initialization completed successfully!"
echo "Buckets created:"
mc ls local
