FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app

LABEL org.opencontainers.image.source="https://github.com/brendanbank/gpsd-prometheus-exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for the gpsd GPS daemon. Collects metrics from the gpsd server and exposes them for scraping."
LABEL org.opencontainers.image.licenses="BSD-3-Clause"

# Build arguments for gpsd version
ARG GPSD_VERSION=3.26.1
ARG GPSD_REPO=https://gitlab.com/gpsd/gpsd.git

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    scons \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps from PyPI
RUN pip install --no-cache-dir prometheus-client

WORKDIR /app

# Build gps Python module from gpsd source
RUN set -eux && \
    GPSD_TEMP_DIR=/tmp/gpsd && \
    GPSD_INSTALL_DIR=/tmp/gpsd-install && \
    echo "Cloning gpsd repository..." && \
    rm -rf ${GPSD_TEMP_DIR} && \
    git clone ${GPSD_REPO} ${GPSD_TEMP_DIR} && \
    cd ${GPSD_TEMP_DIR} && \
    git checkout -q release-${GPSD_VERSION} && \
    echo "Building and installing Python library only..." && \
    scons install python=yes gpsd=no gpsdclients=no xgps=no libgpsmm=no qt=no shared=yes \
        prefix=${GPSD_INSTALL_DIR} python_libdir=${GPSD_INSTALL_DIR}/lib && \
    echo "Copying Python library to /app/gps..." && \
    cp -r ${GPSD_INSTALL_DIR}/lib/gps /app/gps && \
    echo "Cleaning up build files and dependencies..." && \
    rm -rf ${GPSD_TEMP_DIR} ${GPSD_INSTALL_DIR} && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get remove -y --purge --auto-remove \
        git \
        scons \
        build-essential \
        gcc \
        g++ \
        make \
        libc6-dev \
        linux-libc-dev \
        python3-dev \
        python3-distutils \
        && apt-get clean && \
    rm -rf /var/lib/apt/lists/* \
           /tmp/* \
           /var/tmp/* \
           /usr/share/doc/* \
           /usr/share/man/* \
           /usr/share/locale/* \
           /root/.cache \
           /root/.gitconfig && \
    find /usr -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /usr -name "*.a" -delete 2>/dev/null || true

# Copy only required runtime files
COPY entrypoint.sh /app/
COPY gpsd_exporter.py /app/

RUN chmod +x /app/entrypoint.sh

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

