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
  - [Native Installation](#native-installation)
  - [Docker](#docker)
- [Configuration](#configuration)
  - [Command Line Options](#command-line-options)
- [Usage](#usage)
  - [Testing the Exporter](#testing-the-exporter)
  - [Prometheus Integration](#prometheus-integration)
  - [Grafana Dashboard](#grafana-dashboard)
- [License](#license)
- [Contributing](#contributing)

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

### Native Installation

For systems where Docker is not desired:

#### Prerequisites

Ensure gpsd, Prometheus, and Grafana are properly running. For gpsd installation instructions, see the [gpsd official documentation](https://gpsd.gitlab.io/gpsd/installation.html).

The exporter requires:

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

### Docker

For complete Docker installation instructions, configuration options, and platform-specific setup, see [README_DOCKER.md](README_DOCKER.md).

## Configuration

### Command Line Options

```bash
usage: gpsd_exporter.py [-h] [-v] [-V] [-d] [-p PORT] [-H HOSTNAME] [-E EXPORTER_PORT]
                        [-L LISTEN_ADDRESS] [-t TIMEOUT]
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
  -L LISTEN_ADDRESS, --listen-address LISTEN_ADDRESS
                        set listen address for the exporter server. Use '::' for
                        IPv4+IPv6 dual-stack, '0.0.0.0' for IPv4-only [default: ::]
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

## Usage

### Testing the Exporter

Once running, test the metrics endpoint:

```bash
curl -s localhost:9015/metrics
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