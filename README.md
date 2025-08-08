![Graphana dashboard](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/grafana_gpsd_dashboard_1.png?raw=true)
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/clock_pps_offset.png?raw=true)
# gpsd-prometheus-exporter


`gpsd-prometheus-exporter` is a [Prometheus](https://prometheus.io/) exporter for the [gpsd](https://gpsd.gitlab.io/gpsd/) GPS daemon. 

It connects to the TCP port of the GPSD daemon and records relevant statistics and formats them as an Prometheus data exporter which you can visualze later in tools like [grafana](https://grafana.com/).

![Graphana dashboard DOP](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/dop.png?raw=true)


## Installation:

Make sure gpsd, prometheus and grafana are properly running. `gpsd-prometheus-exporter`needs `python3` and the following python libraries:

* [prometheus_client](https://github.com/prometheus/client_python)
* gps-python libraries [gps](https://gpsd.gitlab.io/gpsd/) Note that this exporter needs at least version 3.18 of the lib's. Normally this comes with the installation of gpsd. 

To install:

	apt update
	apt install python3-prometheus-client
	apt install python3-gps

If you want the `gpsd-prometheus-exporter` to be loaded automatically by `systemd` please copy `gpsd_monitor.defaults` to 
`/etc/default/gpsd_monitor.defaults` and `gpsd_monitor.service` to `/lib/systemd/system`

	git clone https://github.com/brendanbank/gpsd-prometheus-exporter.git
	cd gpsd-prometheus-exporter
	cp gpsd_exporter.defaults /etc/default
	cp gpsd_exporter.service /etc/systemd/system
	cp gpsd_exporter.py /usr/local/bin

Make sure `gpsd_exporter.py` has the execution bit set:

	chmod +x /usr/local/bin/gpsd_exporter.py
	
And enable the service to run at boot.
	
	systemctl enable gpsd_exporter.service
	systemctl start gpsd_exporter.service
	
Some U-Blox GPS units need to be forced to 115200 baud

Check out [gps_setserial.service](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/master/gps_setserial.service) to run at boot time. 
	
The default tcp port is 9015. You can test if the exporter is up by running the follwing command on the local machine:

	curl -s localhost:9015
	
And you should see output like this:

	# HELP gpsd_gdop Geometric (hyperspherical) dilution of precision
	# TYPE gpsd_gdop gauge
	gpsd_gdop 1.36
	# HELP gpsd_hdop Horizontal dilution of precision
	# TYPE gpsd_hdop gauge
	gpsd_hdop 0.74
	gpsd_xdop 0.39
	# HELP gpsd_nSat Number of satellite objects in "satellites" array
	# TYPE gpsd_nSat gauge
	gpsd_nSat 0.0
	# HELP gpsd_uSat Number of satellites used in navigation solution.
	# TYPE gpsd_uSat gauge
	gpsd_uSat 0.0
	# HELP gpsd_lat Latitude in degrees: +/- signifies North/South.
	# TYPE gpsd_lat gauge
	gpsd_lat 52.4240029
	# HELP gpsd_long Longitude in degrees: +/- signifies East/West.
	# TYPE gpsd_long gauge
	gpsd_long 4.6157675
	# HELP gpsd_altHAE Altitude, height above allipsoid, in meters. Probably WGS84.
	# TYPE gpsd_altHAE gauge
	gpsd_altHAE 62.191
	# HELP gpsd_altMSL MSL Altitude in meters. The geoid used is rarely specified and is often inaccurate.
	# TYPE gpsd_altMSL gauge
	gpsd_altMSL 16.309
	# HELP gpsd_sat_used Used in current solution? 
	# TYPE gpsd_sat_used gauge
	gpsd_sat_used 19.0
	# HELP gpsd_sat_seen Seen in current solution? 
	# TYPE gpsd_sat_seen gauge
	gpsd_sat_seen 34.0
	# HELP gpsd_version_info Version Details
	# TYPE gpsd_version_info gauge
	gpsd_version_info{proto_major="3",proto_minor="14",release="3.20",rev="3.20"} 1.0
	# HELP gpsd_devices_info Device Details
	# TYPE gpsd_devices_info gauge
	gpsd_devices_info{activated="2021-01-20T12:22:31.083Z",bps="115200",cycle="1.0",device="/dev/ttyS0",driver="u-blox",flags="1",mincycle="0.25",native="1",parity="N",stopbits="1",subtype="SW ROM CORE 3.01 (107888),HW 00080000",subtype1=",FWVER=SPG 3.01,PROTVER=18.00,GPS;GLO;GAL;BDS,SBAS;IMES;QZSS"} 1.0
	gpsd_devices_info{activated="2021-01-20T12:22:31.003Z",bps="Unknown",cycle="Unknown",device="/dev/pps0",driver="PPS",flags="Unknown",mincycle="Unknown",native="Unknown",parity="Unknown",stopbits="Unknown",subtype="Unknown",subtype1="Unknown"} 1.0
	...

To make sure prometheus is polling the exporter add the following line to `/etc/prometheus/prometheus.yml` on the prometheus server.

	  - job_name: gps
    	static_configs:
        - targets: 
                - <hostname>:9015

Be careful not to break with the yml document format as it will block propper startup of prometheus.

I've included a [grafana dashboard json file](https://raw.githubusercontent.com/brendanbank/gpsd-prometheus-exporter/main/gpsd_grafana_dashboard.json) which you can load into grafana.

 
## Per Satellite data
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/sats.png?raw=true)

## PPS
![](https://github.com/brendanbank/gpsd-exporter/raw/master/img/clock_pps_offset.png?raw=true)

If you enable gpsd to monitor your pps device by starting

	gpsd <option> [serial port path] [/dev/pps[0-..]

the exporter will monitor the clock offset from from the pps signal. And you can monitor the offset of your system clock.

To enable pps monitoring add `--pps-histogram` to the runtime arguments of `gpsd_exporter.py`

## Graph offset from a stationary
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/geo_offset.png?raw=true)

## runtime commands


	usage: gpsd_exporter.py [-h] [-v] [-V] [-d] [-p PORT] [-H HOSTNAME] [-E EXPORTER_PORT] [-t TIMEOUT]
	                        [--retry-delay RETRY_DELAY] [--max-retry-delay MAX_RETRY_DELAY] [-S]
	                        [--offset-from-geopoint] [--geopoint-lat GEO_LAT] [--geopoint-lon GEO_LON]
	                        [--geo-bucket-size GEO_BUCKET_SIZE] [--geo-bucket-count GEO_BUCKET_COUNT]
	                        [--pps-histogram] [--pps-bucket-size PPS_BUCKET_SIZE]
	                        [--pps-bucket-count PPS_BUCKET_COUNT] [--pps-time1 PPS_TIME1]
	
	gpsd_exporter -- Exporter for gpsd output
	
	  Created by Brendan Bank on 2021-01-10.
	  Copyright 2021 Brendan Bank. All rights reserved.
	
	  Licensed under the BSD-3-Clause
	  https://opensource.org/licenses/BSD-3-Clause
	
	  Distributed on an "AS IS" basis without warranties
	  or conditions of any kind, either express or implied.
	
	USAGE
	
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
	
## Docker 

You can run this software with docker. 

### Docker Run

    docker run -d --name gpsd-exporter \
        -p 9015:9015 \
        -e GPSD_HOST=192.168.1.10 \
        -e GPSD_PORT=2947 \
        -e GEOPOINT_LON=38.897809878 \
        -e GEOPOINT_LAT=-77.036551259 \
        -e PPS_BUCKET_SIZE=50000 \
        -e PPS_BUCKET_COUNT=40 \
        -e PPS_TIME1=0.123 \
        -e GEO_BUCKET_SIZE=0.5 \
        -e GEO_BUCKET_COUNT=40 \
        -e EXPORTER_PORT=9015 \
        -e VERBOSE=1 \
        -e DEBUG=0 \
        ghcr.io/brendanbank/gpsd-prometheus-exporter:latest

### Docker Compose

Two Docker Compose files are provided:

1. **`docker-compose.yml`** - Uses pre-built image from GitHub Container Registry
2. **`docker-compose.build.yml`** - Builds image locally with enhanced features

#### Using Pre-built Image

To use the pre-built image from GitHub Container Registry:

```bash
docker compose up -d
```

#### Building Locally

To build the image locally with enhanced features:

```bash
docker compose -f docker-compose.build.yml up --build
```

#### Using Environment Variables

The docker-compose files are configured to read environment variables. You can create a `.env` file in the same directory with your configuration:

```bash
# Create .env file
cat > .env << EOF
GPSD_HOST=localhost
GPSD_PORT=2947
GEOPOINT_LON=38.897809878
GEOPOINT_LAT=-77.036551259
PPS_BUCKET_SIZE=50000
PPS_BUCKET_COUNT=40
PPS_TIME1=0.123
GEO_BUCKET_SIZE=0.5
GEO_BUCKET_COUNT=40
EXPORTER_PORT=9015
VERBOSE=1
DEBUG=0
EOF
```

Then run:

```bash
# Using pre-built image from registry
docker compose up -d

# Or build locally with enhanced features
docker compose -f docker-compose.build.yml up --build
```

#### Environment Variables

The following environment variables are supported:

| Variable | Default | Description |
|----------|---------|-------------|
| `GPSD_HOST` | `localhost` | gpsd hostname/IP address |
| `GPSD_PORT` | `2947` | gpsd TCP port |
| `EXPORTER_PORT` | `9015` | Prometheus exporter port |
| `GEOPOINT_LON` | `38.897809878` | Reference longitude for offset calculation |
| `GEOPOINT_LAT` | `-77.036551259` | Reference latitude for offset calculation |
| `PPS_BUCKET_SIZE` | `50000` | PPS histogram bucket size in nanoseconds |
| `PPS_TIME1` | (not set) | PPS time1 offset (enables PPS histogram when set) |
| `VERBOSE` | `1` | Enable verbose output (any value = verbose) |
| `DEBUG` | `0` | Debug level (0 = no debug, 1+ = debug) |
| `GEO_BUCKET_SIZE` | `0.5` | Geo offset histogram bucket size in meters |
| `GEO_BUCKET_COUNT` | `40` | Geo offset histogram bucket count |
| `PPS_BUCKET_COUNT` | `40` | PPS histogram bucket count |

#### Direct Configuration

For pre-built image (`docker-compose.yml`):

    gpsd-exporter:
        image: ghcr.io/brendanbank/gpsd-prometheus-exporter:latest
        container_name: gpsd-exporter
        ports:
            - 9015:9015
        environment:
            - GPSD_HOST=host.docker.internal
            - GPSD_PORT=2947
            - GEOPOINT_LON=38.897809878
            - GEOPOINT_LAT=-77.036551259
            - PPS_BUCKET_SIZE=50000
            - PPS_BUCKET_COUNT=40
            - PPS_TIME1=0.123
            - GEO_BUCKET_SIZE=0.5
            - GEO_BUCKET_COUNT=40
            - EXPORTER_PORT=9015
            - VERBOSE=1
            - DEBUG=0
        extra_hosts:
            - "host.docker.internal:host-gateway"
        restart: unless-stopped

For local build (`docker-compose.build.yml`):

    gpsd-exporter:
        build:
          context: .
          dockerfile: Dockerfile
        image: gpsd-prometheus-exporter:stable
        container_name: gpsd-exporter
        ports:
            - 9015:9015
        environment:
            - GPSD_HOST=localhost
            - GPSD_PORT=2947
            - GEOPOINT_LON=38.897809878
            - GEOPOINT_LAT=-77.036551259
            - PPS_BUCKET_SIZE=50000
            - PPS_BUCKET_COUNT=40
            - PPS_TIME1=0.123
            - GEO_BUCKET_SIZE=0.5
            - GEO_BUCKET_COUNT=40
            - EXPORTER_PORT=9015
            - VERBOSE=1
            - DEBUG=0
        restart: unless-stopped
        network_mode: host

### Enhanced Features (Local Build)

The `docker-compose.build.yml` includes enhanced features:

- **Infinite retry with exponential backoff**: Automatically retries connection to gpsd
- **Connection timeout**: Configurable timeout (default 10s)
- **Improved error handling**: Clear error messages, proper exit codes, and robust connection failure recovery
- **Robust connection management**: Properly handles closed sockets, connection failures, and any GPSD read errors
- **Environment variable control**: All features controllable via environment variables
- **Host networking**: Direct access to host services via `network_mode: host`

### GPSd on Host

If the gpsd daemon run directly on the host, you must either use network_mode: host

    # Docker CLI
    --network=host

    # Docker Compose
    network_mode: host

or by adding `host.docker.internal` to connect the host

    # Docker CLI - Remove "-p 9015:9015"
    -e GPSD_HOST=host.docker.internal \
    --add-host=host.docker.internal:host-gateway \


    # Docker compose - Remove `ports:`
    extra_hosts:
        - "host.docker.internal:host-gateway"

    environment:
        - GPSD_HOST=host.docker.internal

Good Luck!