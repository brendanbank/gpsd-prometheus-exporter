# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Prometheus exporter for gpsd (GPS daemon). Single-file Python application (`gpsd_exporter.py`) that connects to gpsd's TCP port and exposes GPS metrics for Prometheus scraping.

## Build & Run Commands

```bash
# Build gps Python module from gpsd source (required for local development)
make all

# Run the exporter locally
python3 gpsd_exporter.py -H localhost -p 2947

# Syntax check (used in CI)
python -m py_compile gpsd_exporter.py

# Docker build
docker build -t gpsd-prometheus-exporter .
docker compose up -d

# Test metrics endpoint
curl -s localhost:9015/metrics
```

## Architecture

### Core Flow
1. `main()` → Parse args → Init Prometheus metrics → Start HTTP server on port 9015 → Enter retry loop
2. `loop_connection()` → Connect to gpsd TCP socket → Call `getPositionData()` continuously
3. `getPositionData()` → Read JSON messages from gpsd → Route to handlers by message type
4. Message handlers (`VERSION`, `PPS`, `DEVICES`, `SKY`, `TPV`) → Update Prometheus metrics

### Key Components

**SatCollector** - Custom Prometheus collector for per-satellite metrics. Uses a queue to buffer satellite data between Prometheus scrapes. Handles GPS receivers that may not report all fields (svid, gnssid).

**Optional Features:**
- Satellite monitoring (default on, `-S` to disable)
- Geographic offset tracking (`--offset-from-geopoint`) - compares position to fixed reference
- PPS histogram (`--pps-histogram`) - records clock offset from PPS signals in nanoseconds

### Design Patterns

- **Exponential backoff retry**: Connection failures trigger retry with backoff (10s initial, 5min max)
- **Graceful degradation**: Missing fields use `.get()` with defaults; continues on individual message failures
- **Privilege dropping**: Switches from root to nobody:nogroup after binding
- **Thread-safe queue**: Satellite data queued from reader, consumed on `/metrics` scrape

## Docker Networking

- **Linux**: Uses host networking (default in docker-compose.yml)
- **macOS/Windows**: Requires bridge networking with `docker-compose.override.yml` (copy from `.example`)

## Dependencies

- `prometheus-client` - Metrics library
- `gps` - Vendored in `./gps/` directory, built from gpsd source via Makefile
- Requires gpsd >= 3.18

## CI/CD

GitHub Actions workflow (`.github/workflows/docker-publish.yml`):
1. Builds gps module once (shared across platforms)
2. Runs syntax check and import smoke test
3. Builds multi-platform Docker images (7 architectures)
4. Security scan with Trivy
5. Pushes to ghcr.io
