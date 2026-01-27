# gpsd-prometheus-exporter

A [Prometheus](https://prometheus.io/) exporter for the [gpsd](https://gpsd.gitlab.io/gpsd/) GPS daemon that provides comprehensive GPS monitoring and visualization capabilities.

![Grafana Dashboard](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/grafana_gpsd_dashboard_1.png?raw=true)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
  - [GPS Position and Quality Metrics](#gps-position-and-quality-metrics)
  - [Per Satellite Data](#per-satellite-data)
  - [PPS Clock Offset Monitoring](#pps-clock-offset-monitoring)
  - [Geographic Offset Tracking](#geographic-offset-tracking)
- [Installation](#installation)
  - [Docker (Recommended)](#docker-recommended)
    - [Quick Start](#quick-start)
    - [Docker Compose](#docker-compose)
    - [Environment Variables](#environment-variables)
    - [Host Network Configuration](#host-network-configuration)
  - [Native Installation](#native-installation)
- [Configuration](#configuration)
  - [Command Line Options](#command-line-options)
- [Usage Examples](#usage-examples)
  - [Basic Docker Setup](#basic-docker-setup)
  - [Local Build](#local-build)
  - [Custom Configuration](#custom-configuration)
  - [Prometheus Integration](#prometheus-integration)
  - [Grafana Dashboard](#grafana-dashboard)

## Overview

`gpsd-prometheus-exporter` connects to the TCP port of the GPSD daemon and records relevant GPS statistics, formatting them as Prometheus metrics for visualization in tools like [Grafana](https://grafana.com/).

The exporter provides real-time monitoring of:
- GPS position accuracy and quality metrics
- Individual satellite data and signal strength
- PPS (Pulse Per Second) clock offset monitoring
- Geographic offset tracking from a reference point

## Features

### GPS Position and Quality Metrics

Monitor GPS accuracy and quality metrics including DOP (Dilution of Precision) values:

![DOP Metrics](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/dop.png?raw=true)

### Per Satellite Data

Track individual satellite performance and signal quality:

![Per Satellite Data](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/sats.png?raw=true)

### PPS Clock Offset Monitoring

Monitor clock offset from PPS (Pulse Per Second) signals:

![PPS Time Offset](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/clock_pps_offset.png?raw=true)

**Note:** This metric reports only the PPS offset as observed by gpsd. It does not measure or guarantee time synchronization accuracy. Actual time synchronization accuracy is managed by ntpd or other time synchronization daemons. The gpsd PPS implementation assumes the PPS signal is perfect, which may not reflect real-world conditions.

To enable PPS monitoring in the exporter, add `--pps-histogram` to the runtime arguments.

### Geographic Offset Tracking

Track position offset from a stationary reference point:

![Geographic Offset](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/geo_offset.png?raw=true)

## Installation

### Docker (Recommended)

The easiest way to run the exporter is using Docker.

#### Quick Start

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

#### Docker Compose

Two Docker Compose files are provided:

**Using Pre-built Image** (`docker-compose.yml`):
```bash
docker compose up -d
```

**Building Locally** (`docker-compose.build.yml`):
```bash
docker compose -f docker-compose.build.yml up --build
```

**Example configurations:**

**Pre-built Image** (`docker-compose.yml`):
```yaml
services:
  gpsd-exporter:
    image: ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
    container_name: gpsd-exporter
    ports:
      - "${EXPORTER_PORT:-9015}:9015"
    environment:
      - GPSD_HOST=${GPSD_HOST:-host.docker.internal}
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
    extra_hosts:
      - "host.docker.internal:host-gateway"
    dns:
      - 8.8.8.8
      - 8.8.4.4
    restart: unless-stopped
    # Note: network_mode: host only works on Linux, not macOS/Windows
    # For Linux, uncomment the line below and remove the ports: section
    # network_mode: host
```

**Local Build** (`docker-compose.build.yml`):
```yaml
services:
  gpsd-exporter:
    build:
      context: .
      dockerfile: Dockerfile
    image: gpsd-prometheus-exporter:stable
    container_name: gpsd-exporter
    ports:
      - "${EXPORTER_PORT:-9015}:9015"
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
    dns:
      - 8.8.8.8
      - 8.8.4.4
    restart: unless-stopped
    # Note: network_mode: host only works on Linux, not macOS/Windows
    # For Linux, uncomment the line below and remove the ports: section
    # network_mode: host
```

#### Host Network Configuration

- Linux (supports host networking):

```bash
docker run -d --name gpsd-exporter \
  --network=host \
  -e GPSD_HOST=localhost \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

# Access metrics directly on the host
curl 127.0.0.1:9015
```

Docker Compose on Linux can use `network_mode: host` (as shown in the examples above). When using host networking, omit any `ports:` mappings as they are ignored.

- macOS (host networking is not supported):

```bash
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  -e GPSD_HOST=host.docker.internal \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

# Access metrics via the published port
curl 127.0.0.1:9015
```

For Docker Compose on macOS, remove `network_mode: host`, keep `ports:` and `extra_hosts`, add DNS configuration, and set `GPSD_HOST=host.docker.internal`:

```yaml
services:
  gpsd-exporter:
    ports:
      - "9015:9015"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    dns:
      - 8.8.8.8
      - 8.8.4.4
    environment:
      - GPSD_HOST=host.docker.internal
      - GPSD_PORT=2947
```

**Remote gpsd (any OS):** If your gpsd runs on a remote host (e.g., `ntp0.bgwlan.nl`), host networking is not required. Publish the port, configure DNS, and point `GPSD_HOST` to the remote server:

```bash
docker run -d --name gpsd-exporter \
  -p 9015:9015 \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  -e GPSD_HOST=ntp0.bgwlan.nl \
  -e GPSD_PORT=2947 \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
```

Or with Docker Compose for remote gpsd:
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

#### Environment Variables

The following environment variables are supported for Docker deployments:

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

Create a `.env` file for configuration:

```bash
# Create .env file
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

### Native Installation

For systems where Docker is not desired:

#### Prerequisites

Ensure gpsd, Prometheus, and Grafana are properly running. The exporter requires:

- Python 3
- [prometheus_client](https://github.com/prometheus/client_python)
- [gps](https://gpsd.gitlab.io/gpsd/) library (version 3.18+)

#### Installation Steps

```bash
# Install dependencies
apt update
apt install python3-prometheus-client python3-gps

# Note: System python3-gps package may be older than required version 3.18+
# If you encounter version issues, build the gps module from source using the Makefile:
# make all

# Clone repository
git clone https://github.com/brendanbank/gpsd-prometheus-exporter.git
cd gpsd-prometheus-exporter

# Install service files
cp gpsd_exporter.defaults /etc/default
cp gpsd_exporter.service /etc/systemd/system
cp gpsd_exporter.py /usr/local/bin
chmod +x /usr/local/bin/gpsd_exporter.py

# Enable and start service
systemctl enable gpsd_exporter.service
systemctl start gpsd_exporter.service
```

## Configuration

### Command Line Options

```bash
usage: gpsd_exporter.py [-h] [-v] [-V] [-d] [-p PORT] [-H HOSTNAME] [-E EXPORTER_PORT] [-t TIMEOUT]
                        [--retry-delay RETRY_DELAY] [--max-retry-delay MAX_RETRY_DELAY] [-S]
                        [--offset-from-geopoint] [--geopoint-lat GEO_LAT] [--geopoint-lon GEO_LON]
                        [--geo-bucket-size GEO_BUCKET_SIZE] [--geo-bucket-count GEO_BUCKET_COUNT]
                        [--pps-histogram] [--pps-bucket-size PPS_BUCKET_SIZE]
                        [--pps-bucket-count PPS_BUCKET_COUNT] [--pps-time1 PPS_TIME1]

gpsd_exporter -- Exporter for gpsd output

options:
  -h, --help            show this help message and exit
  -v, --verbose         set verbosity level [default: None]
  -V, --version         show program's version number and exit
  -d, --debug           set debug level [default: 0]
  -p PORT, --port PORT  set gpsd TCP Port number [default: 2947]
  -H HOSTNAME, --hostname HOSTNAME
                        set gpsd TCP Hostname/IP address [default: localhost]
  -E EXPORTER_PORT, --exporter-port EXPORTER_PORT
                        set TCP Port for the exporter server [default: 9015]
  -t TIMEOUT, --timeout TIMEOUT
                        set connection timeout in seconds [default: 10]
  --retry-delay RETRY_DELAY
                        initial retry delay in seconds [default: 10]
  --max-retry-delay MAX_RETRY_DELAY
                        maximum retry delay in seconds [default: 300]
  -S, --disable-monitor-satellites
                        Stops monitoring all satellites individually
  --offset-from-geopoint
                        track offset (x,y offset and distance) from a stationary location.
  --geopoint-lat GEO_LAT
                        Latitude of a fixed stationary location.
  --geopoint-lon GEO_LON
                        Longitude of a fixed stationary location.
  --geo-bucket-size GEO_BUCKET_SIZE
                        Bucket side of Geo histogram [default: 0.5 meter]
  --geo-bucket-count GEO_BUCKET_COUNT
                        Bucket count of Geo histogram [default: 40]
  --pps-histogram       generate histogram data from pps devices.
  --pps-bucket-size PPS_BUCKET_SIZE
                        Bucket side of PPS histogram in nanoseconds. [default: 250 ns]
  --pps-bucket-count PPS_BUCKET_COUNT
                        Bucket count of PPS histogram [default: 40]
  --pps-time1 PPS_TIME1
                        Local pps clock (offset) time1 (ntp.conf) [default: 0]
```

## Usage Examples

### Basic Docker Setup

Test the exporter with a simple Docker run:

```bash
curl -s localhost:9015
```

Expected output:
```
# HELP gpsd_gdop Geometric (hyperspherical) dilution of precision
# TYPE gpsd_gdop gauge
gpsd_gdop 1.36
# HELP gpsd_hdop Horizontal dilution of precision
# TYPE gpsd_hdop gauge
gpsd_hdop 0.74
# HELP gpsd_lat Latitude in degrees: +/- signifies North/South.
# TYPE gpsd_lat gauge
gpsd_lat 52.4240029
# HELP gpsd_long Longitude in degrees: +/- signifies East/West.
# TYPE gpsd_long gauge
gpsd_long 4.6157675
...
```

### Local Build

Build the Docker image locally with enhanced features.

**Prerequisites:** The gps Python module must be built before building the Docker image. This avoids rebuilding it for every platform during multi-platform builds.

#### Quick Build (recommended)

Use the helper script that builds the gps module and Docker image:

```bash
./build-docker.sh
```

#### Manual Build

```bash
# Step 1: Build the gps Python module from source
make all

# Step 2: Build Docker image
docker build -t gpsd-prometheus-exporter:local .

# Or use docker-compose
docker compose -f docker-compose.build.yml up --build
```

**Note:** The `gps/` directory is in `.gitignore` and must not be committed to the repository due to licensing requirements.

**Note for macOS users:** The `docker-compose.build.yml` file is configured for bridge networking (works on macOS/Windows). If you're on Linux and want host networking, uncomment `network_mode: host` in the compose file and remove the `ports:` section.

### Prometheus Integration

Add to your Prometheus configuration (`/etc/prometheus/prometheus.yml`):

```yaml
scrape_configs:
  - job_name: gpsd
    static_configs:
      - targets: ['localhost:9015']
    scrape_interval: 15s
```

### Grafana Dashboard

Import the provided [Grafana dashboard JSON](https://raw.githubusercontent.com/brendanbank/gpsd-prometheus-exporter/refs/heads/master/gpsd_grafana_dashboard.json) into Grafana for comprehensive GPS monitoring visualization.

## License

Licensed under the BSD-3-Clause License. See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.