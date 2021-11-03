![Graphana dashboard](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/grafana_gpsd_dashboard_1.png?raw=true)
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/clock_pps_offset.png?raw=true)
# gpsd-prometheus-exporter


`gpsd-prometheus-exporter` is a [Prometheus](https://prometheus.io/) exporter for the [gpsd](https://gpsd.gitlab.io/gpsd/) GPS daemon. 

It connects to the TCP port of the GPSD daemon and records relevant statistics and formats them as an Prometheus data exporter which you can visualze later in tools like [grafana](https://grafana.com/).

![Graphana dashboard DOP](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/dop.png?raw=true)


## Instalation:

Make sure gpsd, prometheus and grafana are properly running. `gpsd-prometheus-exporter`needs `python3` and the following python libraries:

* [prometheus_client](https://github.com/prometheus/client_python)
* gps-python libraries [gps](https://gpsd.gitlab.io/gpsd/) Note that this exporter needs at least version 3.19 of the lib's. Normally this comes with the instalation of gpsd.

To install:

	pip3 install prometheus_client
	pip3 install gps

If you want the `gpsd-prometheus-exporter` to be loaded automatically by `systemd` please copy `gpsd_monitor.defaults` to 
`/etc/default/gpsd_monitor.defaults` and `gpsd_monitor.service` to `/lib/systemd/system`

	git clone git@github.com:brendanbank/gpsd-prometheus-exporter.git
	cd gpsd-prometheus-exporter
	sudo cp gpsd_exporter.defaults /etc/default
	sudo cp gpsd_exporter.service /lib/systemd/system
	sudo cp gpsd_exporter.py /usr/local/bin

Make sure `gpsd_exporter.py` has the execution bit set:

	chmod +x /usr/local/bin/gpsd_exporter.py
	
And enable the serivce to run at boot.
	
	systemctl enable gpsd_exporter.service
	systemctl start gpsd_exporter.service
	
Some U-Blox GPS units need to be forced to 115200 baud

Check out [gps_setserial.serivce](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/master/gps_setserial.service) to run at boot time. 
	
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

To make sure prometheus is polling the exporter add the following line to `/etc/prometheus/prometeus.yml` on the prometheus server.

	  - job_name: gps
    	static_configs:
        - targets: 
                - <hostname>:9015

Be carefull not to break with the yml document format as it will block propper startup of prometheus.

I've included a [grafana dashboard json file](https://raw.githubusercontent.com/brendanbank/gpsd-prometheus-exporter/main/gpsd_grafana_dashboard.json) which you can load into grafana.

 
## Per Satilite data
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/sats.png?raw=true)

## PPS
![](https://github.com/brendanbank/gpsd-exporter/raw/master/img/clock_pps_offset.png?raw=true)

If you enable gpsd to monitor your pps device by starting

	gpsd <option> [serial port path] [/dev/pps[0-..]

the exporter will monitor the clock offset from from the pps signal. And you can monitor the offset of your system clock.

To eable pps monitoring add `--pps-histogram` to the runtime arguments of `gpsd_exporter.py`

## Graph offset from a stationairy
![](https://github.com/brendanbank/gpsd-prometheus-exporter/blob/ce8d05be537ec7fe935bad0c9479cf3e0770b41a/img/geo_offset.png?raw=true)

## runtime commands


	./gpsd_exporter.py -h
	usage: gpsd_exporter.py [-h] [-v] [-V] [-d] [-p PORT] [-E EXPORTER_PORT] [-H HOSTNAME] 
	[-S] [--offset-from-geopoint] [--geopoint-lat GEO_LAT] [--geopoint-lon GEO_LON] 
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
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -v, --verbose         set verbosity level [default: None]
	  -V, --version         show program's version number and exit
	  -d, --debug           set debug level [default: 0]
	  -p PORT, --port PORT  set gpsd TCP Port number to connect to [default: 2947]
	  -H HOSTNAME, --hostname HOSTNAME
	                        set gpsd  TCP Hostname/IP address [default: localhost]
	  -E EXPORTER_PORT, --exporter-port EXPORTER_PORT
	                        set TCP Port for the exporter server [default: 9015]
	  -S, --disable-monitor-satellites
	                        Stops monitoring all satellites individually
	  --offset-from-geopoint
	                        track offset (x,y and distance) from a stationary location.
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
	                        Bucket side of PPS histogram [default: 250 ns] (nano seconds)
	  --pps-bucket-count PPS_BUCKET_COUNT
	                        Bucket count of PPS histogram [default: 40]
	  --pps-time1 PPS_TIME1
	                        Local pps clock (offset) time1 (ntp.conf) [default: 0]
