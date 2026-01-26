#!/bin/bash
# Helper script to build Docker image locally
# This ensures the gps module is built before Docker build

set -e

echo "Building gps Python module from source..."
make all

echo ""
echo "Building Docker image..."
docker build -t gpsd-prometheus-exporter:local .

echo ""
echo "Build completed successfully!"
echo "Run with: docker run --rm gpsd-prometheus-exporter:local --help"
