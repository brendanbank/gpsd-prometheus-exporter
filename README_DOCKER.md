# Docker Installation Guide

This guide covers all Docker-related installation and configuration options for gpsd-prometheus-exporter.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Compose](#docker-compose)
  - [Using Pre-built Image](#using-pre-built-image)
  - [Building Locally](#building-locally)
  - [macOS/Windows Bridge Networking](#macoswindows-bridge-networking)
- [Environment Variables](#environment-variables)
- [Platform-Specific Configuration](#platform-specific-configuration)
  - [Linux](#linux)
  - [macOS/Windows](#macoswindows)
  - [Remote gpsd Server](#remote-gpsd-server)
- [Local Build](#local-build)

## Quick Start

The easiest way to run the exporter is using Docker with the pre-built image.

**Linux (with host networking):**
```bash
docker run -d --name gpsd-exporter \
    --network=host \
    -e GPSD_HOST=localhost \
    -e GPSD_PORT=2947 \
    -e GEOPOINT_LON=38.897809878 \
    -e GEOPOINT_LAT=-77.036551259 \
    -e PPS_BUCKET_SIZE=250 \
    -e PPS_BUCKET_COUNT=40 \
    -e GEO_BUCKET_SIZE=0.5 \
    -e GEO_BUCKET_COUNT=40 \
    -e VERBOSE=1 \
    -e DEBUG=0 \
    ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

# Note: With host networking, EXPORTER_PORT is not needed
# The exporter binds directly to port 9015 on the host
```

**macOS/Windows (bridge networking):**
```bash
docker run -d --name gpsd-exporter \
    -p 9015:9015 \
    -e GPSD_HOST=host.docker.internal \
    -e GPSD_PORT=2947 \
    -e GEOPOINT_LON=38.897809878 \
    -e GEOPOINT_LAT=-77.036551259 \
    -e PPS_BUCKET_SIZE=250 \
    -e PPS_BUCKET_COUNT=40 \
    -e GEO_BUCKET_SIZE=0.5 \
    -e GEO_BUCKET_COUNT=40 \
    -e EXPORTER_PORT=9015 \
    -e VERBOSE=1 \
    -e DEBUG=0 \
    ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
```

Test the exporter:
```bash
curl -s localhost:9015/metrics
```

## Docker Compose

Two Docker Compose files are provided for different use cases.

### Using Pre-built Image

Use `docker-compose.yml` to run the latest pre-built image from GitHub Container Registry.

**Linux (default):**
```bash
docker compose up -d
```

**macOS/Windows:**
```bash
# First time only: Copy the override file for bridge networking
cp docker-compose.override.yml.example docker-compose.override.yml

# Then run normally
docker compose up -d
```

**Configuration** (`docker-compose.yml`):
```yaml
services:
  gpsd-exporter:
    image: ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
    container_name: gpsd-exporter
    network_mode: host  # Default for Linux
    environment:
      - GPSD_HOST=${GPSD_HOST:-localhost}
      - GPSD_PORT=${GPSD_PORT:-2947}
      - GEOPOINT_LON=${GEOPOINT_LON:-38.897809878}
      - GEOPOINT_LAT=${GEOPOINT_LAT:--77.036551259}
      - PPS_BUCKET_SIZE=${PPS_BUCKET_SIZE:-250}
      - PPS_BUCKET_COUNT=${PPS_BUCKET_COUNT:-40}
      - PPS_TIME1=${PPS_TIME1}
      - GEO_BUCKET_SIZE=${GEO_BUCKET_SIZE:-0.5}
      - GEO_BUCKET_COUNT=${GEO_BUCKET_COUNT:-40}
      - EXPORTER_PORT=${EXPORTER_PORT:-9015}
      - DEBUG=${DEBUG:-0}
      - VERBOSE=${VERBOSE:-1}
    restart: unless-stopped
    # Note: This uses host networking (default for Linux)
    # macOS/Windows users: Copy docker-compose.override.yml.example to docker-compose.override.yml
```

Create a `.env` file for customization:

```bash
cat > .env << EOF
GPSD_HOST=localhost
GPSD_PORT=2947
GEOPOINT_LON=38.897809878
GEOPOINT_LAT=-77.036551259
PPS_BUCKET_SIZE=250
PPS_BUCKET_COUNT=40
PPS_TIME1=0.123
GEO_BUCKET_SIZE=0.5
GEO_BUCKET_COUNT=40
EXPORTER_PORT=9015
VERBOSE=1
DEBUG=0
EOF
```

### Building Locally

Use `docker-compose.build.yml` to build the image from source.

**Linux:**
```bash
docker compose -f docker-compose.build.yml up --build
```

**macOS/Windows:**
```bash
# First time only: Copy the override file
cp docker-compose.override.yml.example docker-compose.override.yml

# Build and run
docker compose -f docker-compose.build.yml up --build
```

**Configuration** (`docker-compose.build.yml`):
```yaml
services:
  gpsd-exporter:
    build:
      context: .
      dockerfile: Dockerfile
    image: gpsd-prometheus-exporter:stable
    container_name: gpsd-exporter
    network_mode: host  # Default for Linux
    environment:
      - GPSD_HOST=${GPSD_HOST:-localhost}
      - GPSD_PORT=${GPSD_PORT:-2947}
      - GEOPOINT_LON=${GEOPOINT_LON:-38.897809878}
      - GEOPOINT_LAT=${GEOPOINT_LAT:--77.036551259}
      - PPS_BUCKET_SIZE=${PPS_BUCKET_SIZE:-250}
      - PPS_BUCKET_COUNT=${PPS_BUCKET_COUNT:-40}
      - PPS_TIME1=${PPS_TIME1}
      - GEO_BUCKET_SIZE=${GEO_BUCKET_SIZE:-0.5}
      - GEO_BUCKET_COUNT=${GEO_BUCKET_COUNT:-40}
      - EXPORTER_PORT=${EXPORTER_PORT:-9015}
      - DEBUG=${DEBUG:-0}
      - VERBOSE=${VERBOSE:-1}
    restart: unless-stopped
    # Note: This uses host networking (default for Linux)
    # macOS/Windows users: Copy docker-compose.override.yml.example to docker-compose.override.yml
```

### macOS/Windows Bridge Networking

macOS and Windows users must use bridge networking as host mode is not supported on Docker Desktop.

**Setup (first time only):**

1. Copy the example override file:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

2. Run Docker Compose normally:
```bash
docker compose up -d
```

The override file automatically configures bridge networking for Docker Desktop. When using bridge networking:
- Port 9015 is mapped to the host
- Uses `host.docker.internal` to reach services on the host machine
- DNS is properly configured for name resolution

**Why is an override needed?** The default `docker-compose.yml` uses host networking for optimal performance on Linux. Docker Desktop on macOS/Windows uses a VM, so host networking doesn't work. The override file switches to bridge networking and adjusts the configuration accordingly.

## Environment Variables

Configure the exporter using environment variables in your `.env` file or docker-compose configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `GPSD_HOST` | `localhost` | gpsd hostname/IP address |
| `GPSD_PORT` | `2947` | gpsd TCP port |
| `EXPORTER_PORT` | `9015` | Prometheus exporter port |
| `GEOPOINT_LON` | `38.897809878` | Reference longitude for offset calculation |
| `GEOPOINT_LAT` | `-77.036551259` | Reference latitude for offset calculation |
| `PPS_BUCKET_SIZE` | `250` | PPS histogram bucket size in nanoseconds |
| `PPS_TIME1` | (not set) | PPS time1 offset (enables PPS histogram when set) |
| `VERBOSE` | `1` | Enable verbose output (any value = verbose) |
| `DEBUG` | `0` | Debug level (0 = no debug, 1+ = debug) |
| `GEO_BUCKET_SIZE` | `0.5` | Geo offset histogram bucket size in meters |
| `GEO_BUCKET_COUNT` | `40` | Geo offset histogram bucket count |
| `PPS_BUCKET_COUNT` | `40` | PPS histogram bucket count |

## Platform-Specific Configuration

### Linux

Linux supports both bridge and host networking modes. **Host networking is the default** and provides the best performance.

**Host Networking (Default):**
```bash
docker run -d --name gpsd-exporter \
  --network=host \
  -e GPSD_HOST=localhost \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

# Access metrics directly on the host
curl 127.0.0.1:9015/metrics
```

For Docker Compose, simply run:
```bash
docker compose up -d
```

The default configuration uses host networking. Benefits:
- Lower latency between containers and host services
- Direct access to host network interfaces
- No NAT overhead
- No port mapping required

**Bridge Networking (Optional):**
If you need bridge networking on Linux (e.g., for network isolation):
```bash
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  -e GPSD_HOST=localhost \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
```

### macOS/Windows

macOS and Windows require bridge networking as host mode is not supported on Docker Desktop.

```bash
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  -e GPSD_HOST=host.docker.internal \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

# Access metrics via the published port
curl 127.0.0.1:9015/metrics
```

For Docker Compose, copy the override file first:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker compose up -d
```

The override file configures:
- Bridge networking mode
- Port mapping (9015:9015)
- `host.docker.internal` for reaching the host
- DNS configuration

### Remote gpsd Server

For remote gpsd servers (any OS), use bridge networking with DNS configuration:

```bash
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  -e GPSD_HOST=ntp0.bgwlan.nl \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
```

Docker Compose configuration:
```yaml
services:
  gpsd-exporter:
    image: ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
    ports:
      - "9015:9015"
    dns:
      - 8.8.8.8
      - 8.8.4.4
    environment:
      - GPSD_HOST=ntp0.bgwlan.nl
      - GPSD_PORT=2947
```

## Local Build

Build the Docker image locally with enhanced features.

### Prerequisites

The gps Python module must be built before building the Docker image. This avoids rebuilding it for every platform during multi-platform builds.

### Quick Build (Recommended)

Use the helper script that builds the gps module and Docker image:

```bash
./build-docker.sh
```

### Manual Build

```bash
# Step 1: Build the gps Python module from source
make all

# Step 2: Build Docker image
docker build -t gpsd-prometheus-exporter:local .

# Or use docker-compose
docker compose -f docker-compose.build.yml up --build
```

**Note:** The `gps/` directory is in `.gitignore` and must not be committed to the repository due to licensing requirements.

### Testing the Local Build

```bash
# Run the locally built image
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  -e GPSD_HOST=localhost \
  -e GPSD_PORT=2947 \
  gpsd-prometheus-exporter:local

# Test the metrics endpoint
curl -s localhost:9015/metrics | head -20
```

## Troubleshooting

### Connection Issues

If the exporter cannot connect to gpsd:

1. **Verify gpsd is running:**
   ```bash
   telnet localhost 2947
   ```

2. **Check Docker networking:**
   - Linux with host networking: Use `GPSD_HOST=localhost`
   - macOS/Windows: Use `GPSD_HOST=host.docker.internal`
   - Remote server: Use the hostname or IP address

3. **Check DNS resolution:**
   Add DNS servers to your configuration:
   ```yaml
   dns:
     - 8.8.8.8
     - 8.8.4.4
   ```

### Port Already in Use

If port 9015 is already in use, change the `EXPORTER_PORT`:

```bash
docker run -d --name gpsd-exporter \
  -p 9016:9016 \
  -e EXPORTER_PORT=9016 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
```

### Viewing Logs

Check container logs for issues:

```bash
docker logs gpsd-exporter
```

For continuous log monitoring:

```bash
docker logs -f gpsd-exporter
```

## Next Steps

- Configure [Prometheus](../README.md#prometheus-integration) to scrape metrics
- Import the [Grafana dashboard](../README.md#grafana-dashboard) for visualization
- Review [command line options](../README.md#command-line-options) for advanced configuration
