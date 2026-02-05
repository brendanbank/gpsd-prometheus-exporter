# Optimized Dockerfile for multi-platform builds
# The gps Python module is built once in CI/CD and provided as a build context
# This avoids rebuilding the module for each platform (7+ platforms)

FROM python:3.13-alpine

ENV PYTHONPATH=/app

LABEL org.opencontainers.image.source="https://github.com/brendanbank/gpsd-prometheus-exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for the gpsd GPS daemon. Collects metrics from the gpsd server and exposes them for scraping."
LABEL org.opencontainers.image.licenses="BSD-3-Clause"

# Python deps from PyPI
RUN pip install --no-cache-dir prometheus-client

WORKDIR /app

# Copy pre-built gps module from build context (provided by CI/CD or local build)
# For CI/CD: The gps module is built once and downloaded as an artifact
# For local: Run 'make all' to build the gps module before building the Docker image
COPY gps /app/gps

# Copy only required runtime files
COPY entrypoint.sh /app/
COPY gpsd_exporter.py /app/

RUN chmod +x /app/entrypoint.sh

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

