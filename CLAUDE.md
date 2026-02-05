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

## Networking

- **IPv6**: Exporter binds to `::` (dual-stack) by default via `-L`/`--listen-address` CLI option and `LISTEN_ADDRESS` env var. Accepts both IPv4 and IPv6.
- **gpsd client**: Uses `socket.getaddrinfo()`, supports IPv4 and IPv6 hosts natively.
- **Docker (Linux)**: Uses host networking (default in docker-compose.yml). IPv6 works automatically.
- **Docker (macOS/Windows)**: Requires bridge networking with `docker-compose.override.yml` (copy from `.example`). IPv6 requires enabling `"ipv6": true` in Docker daemon config.

## Dependencies

- `prometheus-client` - Metrics library
- `gps` - Vendored in `./gps/` directory, built from gpsd source via Makefile
- Requires gpsd >= 3.18

## Adding CLI Arguments

When adding a new CLI argument, update all of these:
1. `gpsd_exporter.py` — add `parser.add_argument()` and use in code
2. `entrypoint.sh` — map env var to CLI flag
3. `docker-compose.yml` — add env var with default
4. `docker-compose.build.yml` — same
5. `README.md` — update CLI help output
6. `README_DOCKER.md` — update env var table, compose snippets, and `.env` example

## CI/CD

GitHub Actions workflow (`.github/workflows/docker-publish.yml`):
1. Builds gps module once (shared across platforms)
2. Runs syntax check and import smoke test
3. Builds multi-platform Docker images (7 architectures)
4. Security scan with Trivy
5. Pushes to ghcr.io

## Release Process

1. Bump `__version__` and `__updated__` in `gpsd_exporter.py`
2. Update `RELEASE_NOTES.md`
3. Commit and push to master
4. Create annotated tag: `git tag -a v1.x.x -m "..."`
5. Push tag: `git push origin v1.x.x`
6. CI/CD automatically builds Docker images and creates a GitHub Release
