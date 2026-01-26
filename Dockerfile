# Multi-stage build to optimize build time for multi-platform builds
# Stage 1 builds the gps Python module once (architecture-independent pure Python)
# Stage 2 copies the pre-built module to each platform, avoiding rebuilding for each arch

# Stage 1: Build gps Python module from source (architecture-independent)
FROM python:3.12-slim AS gps-builder

ARG GPSD_VERSION=3.26.1
ARG GPSD_REPO=https://gitlab.com/gpsd/gpsd.git

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    scons \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Build gps Python module from gpsd source
RUN set -eux && \
    GPSD_TEMP_DIR=/tmp/gpsd && \
    GPSD_INSTALL_DIR=/tmp/gpsd-install && \
    echo "Cloning gpsd repository..." && \
    git clone ${GPSD_REPO} ${GPSD_TEMP_DIR} && \
    cd ${GPSD_TEMP_DIR} && \
    git checkout -q release-${GPSD_VERSION} && \
    echo "Building and installing Python library only..." && \
    scons install python=yes gpsd=no gpsdclients=no xgps=no libgpsmm=no qt=no shared=yes \
        prefix=${GPSD_INSTALL_DIR} python_libdir=${GPSD_INSTALL_DIR}/lib && \
    echo "Copying Python library to /gps..." && \
    cp -r ${GPSD_INSTALL_DIR}/lib/gps /gps && \
    echo "Build completed successfully!"

# Stage 2: Final runtime image
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app

LABEL org.opencontainers.image.source="https://github.com/brendanbank/gpsd-prometheus-exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for the gpsd GPS daemon. Collects metrics from the gpsd server and exposes them for scraping."
LABEL org.opencontainers.image.licenses="BSD-3-Clause"

# Python deps from PyPI
RUN pip install --no-cache-dir prometheus-client

WORKDIR /app

# Copy pre-built gps module from builder stage
COPY --from=gps-builder /gps /app/gps

# Copy only required runtime files
COPY entrypoint.sh /app/
COPY gpsd_exporter.py /app/

RUN chmod +x /app/entrypoint.sh

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

