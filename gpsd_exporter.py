#!/usr/bin/env python3
# encoding: utf-8
'''
gpsd_exporter -- Exporter for gpsd output

gpsd_exporter is a data exporter for Prometheus

It defines classes_and_methods

@author:     Brendan Bank

@copyright:  2021 Brendan Bank. All rights reserved.

@license:    BSDv3

@contact:    brendan.bank ... gmail.com
@deffield    updated: Updated
'''

import sys
import os
import gps
import time
import math
import pwd
import grp
import queue
import socket
import json

import logging
from prometheus_client import Histogram, CollectorRegistry, start_http_server, Gauge, Info
from prometheus_client.metrics_core import GaugeMetricFamily
from time import gmtime

log = logging.getLogger(__name__)

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = "1.0.8"
__date__ = '2021-01-10'
__updated__ = '2025-08-08'

DEBUG = 1
TESTRUN = 0
PROFILE = 0
GPSD_PORT = 2947
EXPORTER_PORT = 9015
DEFAULT_HOST = 'localhost'
DEFAULT_TIMEOUT = 10  # Default connection timeout in seconds
DEFAULT_RETRY_DELAY = 10  # Default initial retry delay in seconds
DEFAULT_MAX_RETRY_DELAY = 300  # Maximum retry delay in seconds (5 minutes)
NSEC=1000000000
USEC=1000000
MSEC=1000
    
class DepencendyError(Exception):
    pass

# Monkey patch to handle JSON encoding issues with newer Python versions
try:
    # Try to patch the JSON decoder if needed
    original_init = json.JSONDecoder.__init__
    def patched_init(self, *args, **kwargs):
        # Remove encoding parameter if present (deprecated in Python 3.9+)
        kwargs.pop('encoding', None)
        return original_init(self, *args, **kwargs)
    json.JSONDecoder.__init__ = patched_init
except Exception:
    # If patching fails, continue anyway
    pass

# Check gps version using packaging module (modern approach)
try:
    from packaging import version
    if version.parse(gps.__version__) < version.parse("3.18"):
        raise DepencendyError('Please upgrade the python gps package to 3.18 or higher.')
except ImportError:
    # Fallback to simple string comparison if packaging not available
    try:
        gps_version = gps.__version__.split('.')
        if len(gps_version) >= 2:
            major, minor = int(gps_version[0]), int(gps_version[1])
            if major < 3 or (major == 3 and minor < 18):
                raise DepencendyError('Please upgrade the python gps package to 3.18 or higher.')
    except (ValueError, AttributeError):
        # If version check fails, continue anyway
        pass

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg

class ModuleDepencendyError(ModuleNotFoundError):
    def __init__(self, msg):
        super(ModuleDepencendyError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg

sat_queue = queue.Queue()


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

Created by Brendan Bank on %s.

Copyright 2021 Brendan Bank. All rights reserved.

Licensed under the BSD-3-Clause
https://opensource.org/licenses/BSD-3-Clause

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

Version: %s

Version Date: %s

Usage:
''' % (program_shortdesc, str(__date__), program_version, program_build_date)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count",
                             help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-d', '--debug', action='count', default=0, dest="debug",
                            help="set debug level [default: %(default)s]")
        
        parser.add_argument('-p', '--port', type=int, dest="port", default=GPSD_PORT,
                            help="set gpsd TCP Port number [default: %(default)s]")
        parser.add_argument('-H', '--hostname', dest="hostname", default=DEFAULT_HOST,
                            help="set gpsd TCP Hostname/IP address [default: %(default)s]")
        parser.add_argument('-E', '--exporter-port', type=int, dest="exporter_port", default=EXPORTER_PORT,
                            help="set TCP Port for the exporter server [default: %(default)s]")
        
        parser.add_argument('-t', '--timeout', type=int, dest="timeout", default=DEFAULT_TIMEOUT,
                            help="set connection timeout in seconds [default: %(default)s]")
        
        parser.add_argument('--retry-delay', type=int, dest="retry_delay", default=DEFAULT_RETRY_DELAY,
                            help="initial retry delay in seconds [default: %(default)s]")
        parser.add_argument('--max-retry-delay', type=int, dest="max_retry_delay", default=DEFAULT_MAX_RETRY_DELAY,
                            help="maximum retry delay in seconds [default: %(default)s]")
        
        parser.add_argument('-S', '--disable-monitor-satellites', dest="mon_satellites", 
                            default=True, action="store_false",
                            help="Stops monitoring all satellites individually")
        
        parser.add_argument('--offset-from-geopoint', action="store_true", dest="geo_offset",
                            default=False, help="track offset (x,y offset and distance) from a stationary location.")
        parser.add_argument('--geopoint-lat', dest="geo_lat",type=float,
                            default=False, help="Latitude of a fixed stationary location.")
        parser.add_argument('--geopoint-lon', dest="geo_lon", type=float,
                            default=False, help="Longitude of a fixed stationary location.")
        
        parser.add_argument('--geo-bucket-size', dest="geo_bucket_size", default=0.5, type=float,
                            help="Bucket side of Geo histogram [default: %(default)s meter] ")
        parser.add_argument('--geo-bucket-count', dest="geo_bucket_count", default=40, type=int,
                            help="Bucket count of Geo histogram [default: %(default)s]")

        ## pps
        parser.add_argument('--pps-histogram', action="store_true", dest="pps", default=False,
                            help="generate histogram data from pps devices.")
        parser.add_argument('--pps-bucket-size', dest="pps_bucket_size", default=250, type=int,
                            help="Bucket side of PPS histogram [default: %(default)s ns]  (nano seconds)")
        parser.add_argument('--pps-bucket-count', dest="pps_bucket_count", default=40, type=int,
                            help="Bucket count of PPS histogram [default: %(default)s]")
        parser.add_argument('--pps-time1', dest="pps_time1", default=0, type=float,
                            help="Local pps clock (offset) time1 (ntp.conf) [default: %(default)s]")

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        debug = args.debug

        if (debug > 0):
            logging.basicConfig(format='DEBUG %(funcName)s(%(lineno)s): %(message)s', 
                                stream=sys.stderr, level=logging.DEBUG)
        elif (verbose):
            logging.basicConfig(format=program_name + ': %(message)s', stream=sys.stderr, level=logging.INFO)
        else:
            logging.basicConfig(format=program_name + ': %(message)s', stream=sys.stderr, level=logging.WARN)

        log.info('started')
        
        metrics = init_metrics(args)
        
        start_http_server(args.exporter_port, registry=metrics['registry'])
        
        retry_count = 0
        current_delay = args.retry_delay
        
        while True:
            try:
                loop_connection(metrics, args)
                # If we get here, connection was successful, reset retry count
                retry_count = 0
                current_delay = args.retry_delay
                
            except (KeyboardInterrupt):
                print ("Applications closed!")
                return(0)
            except (StopIteration, ConnectionRefusedError, socket.timeout, ConnectionError, OSError) as e:
                retry_count += 1
                log.error(f'Connection to gpsd failed (attempt {retry_count}): {e}')
                
                print(f'WARNING: Connection failed (attempt {retry_count}), retrying in {current_delay}s...')
                print(f'Connection error: {e}')
                print(f'Error type: {type(e).__name__}')
                
                time.sleep(current_delay)
                
                # Exponential backoff with maximum delay
                current_delay = min(current_delay * 2, args.max_retry_delay)
                
            except Exception as e:
                log.error(f'Unexpected error in main loop: {e}')
                print(f'ERROR: Unexpected error: {e}')
                return(1)

                
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

    
def init_metrics(args):
    
    metrics = {}
    registry = CollectorRegistry()
    
    """ register the Satellite collector who takes the """
    registry.register(SatCollector())

    metrics['SKY'] = {
        'gdop': Gauge('gpsd_gdop', 'Geometric (hyperspherical) dilution of precision', registry=registry),
        'hdop': Gauge('gpsd_hdop', 'Horizontal dilution of precision', registry=registry),
        'pdop': Gauge('gpsd_pdop', 'Position (spherical/3D) dilution of precision', registry=registry),
        'tdop': Gauge('gpsd_tdop', 'Time dilution of precision', registry=registry),
        'vdop': Gauge('gpsd_vdop', 'Vertical (altitude) dilution of precision', registry=registry),
        'ydop': Gauge('gpsd_ydop', 'Longitudinal dilution of precision', registry=registry),
        'xdop': Gauge('gpsd_xdop', 'Latitudinal dilution of precision', registry=registry),
        'nSat': Gauge('gpsd_nSat', 'Number of satellite objects in "satellites" array', registry=registry),
        'uSat': Gauge('gpsd_uSat', 'Number of satellites used in navigation solution.', registry=registry),
    }

    metrics['TPV'] = {
            'lat': Gauge('gpsd_lat', 'Latitude in degrees: +/- signifies North/South.', registry=registry),
            'lon': Gauge('gpsd_long', 'Longitude in degrees: +/- signifies East/West.', registry=registry),
            'altHAE': Gauge('gpsd_altHAE', 'Altitude, height above allipsoid, in meters. Probably WGS84.', 
                            registry=registry),
            'altMSL': Gauge('gpsd_altMSL', 'MSL Altitude in meters. The geoid used is rarely specified and is often inaccurate.' , registry=registry),
            'mode': Gauge('gpsd_mode', 'NMEA mode: %d, 0=no mode value yet seen, 1=no fix, 2=2D, 3=3D.' , 
                          registry=registry),
            'status': Gauge('gpsd_status', 'GPS fix status: %d, 2=DGPS fix, 3=RTK Fixed point, 4=RTK Floating point, 5=DR fix, 6=GNSSDR' + 
                             'fix, 7=Time (surveyed) fix, 8=Simulated, 9=P(Y) fix, otherwise not present. ' , 
                             registry=registry),
            'leapseconds': Gauge('gpsd_leapseconds', 'Current leap seconds.' , registry=registry),
            'magvar': Gauge('gpsd_magvar', 'Magnetic variation, degrees.' , registry=registry),
            'ept': Gauge('gpsd_ept', 'Estimated timestamp error in seconds.' , registry=registry),
            'epx': Gauge('gpsd_epx', 'Longitude error estimate in meters.' , registry=registry),
            'epy': Gauge('gpsd_epy', 'Latitude error estimate in meters.' , registry=registry),
            'epv': Gauge('gpsd_epv', 'Estimated vertical error in meters.' , registry=registry),
            'eps': Gauge('gpsd_eps', 'Estimated speed error in meters per second.' , registry=registry),
            'epc': Gauge('gpsd_epc', 'Estimated climb error in meters per second.' , registry=registry),
            'geoidSep': Gauge('gpsd_geoidSep', 'Geoid separation is the difference between the WGS84 reference ellipsoid and the geoid (Mean Sea Level) in meters. ' , 
                              registry=registry),
            'eph': Gauge('gpsd_eph', 'Estimated horizontal Position (2D) Error in meters. Also known as Estimated Position Error (epe).' , 
                         registry=registry),
            'sep': Gauge('gpsd_sep', 'Estimated Spherical (3D) Position Error in meters.' , registry=registry),
            'ecefx': Gauge('gpsd_ecefx', 'ECEF X position in meters.' , registry=registry),
            'ecefy': Gauge('gpsd_ecefy', 'ECEF Y position in meters.' , registry=registry),
            'ecefz': Gauge('gpsd_ecefz', 'ECEF Z position in meters.' , registry=registry),
            'ecefvx': Gauge('gpsd_ecefvx', 'ECEF X velocity in meters per second.' , registry=registry),
            'ecefvy': Gauge('gpsd_ecefvy', 'ECEF Y velocity in meters per second.' , registry=registry),
            'ecefvz': Gauge('gpsd_ecefvz', 'ECEF Z velocity in meters per second.' , registry=registry),
            'ecefpAcc': Gauge('gpsd_ecefpAcc', 'ECEF position error in meters. Certainty unknown.' , 
                              registry=registry),
            'velN': Gauge('gpsd_velN', 'North velocity component in meters.' , registry=registry),
            'velE': Gauge('gpsd_velE', 'East velocity component in meters.' , registry=registry),
            'velD': Gauge('gpsd_velD', 'Down velocity component in meters.' , registry=registry),
            }

    metrics['USED'] = Gauge('gpsd_sat_used', 'Used in current solution? ', registry=registry)
    metrics['SEEN'] = Gauge('gpsd_sat_seen', 'Seen in current solution? ', registry=registry)
    metrics['VERSION'] = Info('gpsd_version', 'Version Details', registry=registry)
    metrics['DEVICES'] = Info('gpsd_devices', 'Device Details', ['device'], registry=registry)
    metrics['SAT_STATUS'] = {}
    
    if (args.pps):
        PPS_BUCKETS = []
        PPS_BUCKETS.append(float("-inf"))
        [ PPS_BUCKETS.append(i * args.pps_bucket_size) for i in range(int(args.pps_bucket_count / -2), int(args.pps_bucket_count / 2) + 1)]
        PPS_BUCKETS.append(float("inf"))
        metrics['PPS_HIS'] = Histogram('gpsd_pps_histogram', 'PPS Histogram', ['device'], buckets=PPS_BUCKETS, registry=registry)
        
    if args.geo_offset:
        GEO_BUCKETS_OFFSET = []
        [ GEO_BUCKETS_OFFSET.append(i * args.geo_bucket_size) for i in range(1,args.geo_bucket_count)]
        GEO_BUCKETS_OFFSET.append(float("inf"))

        GEO_BUCKETS_YX = []
        GEO_BUCKETS_YX.append(float("-inf"))
        [ GEO_BUCKETS_YX.append(i * args.geo_bucket_size) 
                for i in range(int (args.geo_bucket_count / -2),int(args.geo_bucket_count / 2) + 1)]
        GEO_BUCKETS_YX.append(float("inf"))
        
        metrics['GEO_OFFSET'] = Histogram('gpsd_geo_offset_m_histogram', 'Geo offset Histogram (meters)', 
                                          buckets=GEO_BUCKETS_OFFSET, registry=registry)
        metrics['GEO_OFFSET_Y'] = Histogram('gpsd_geo_bearing_x_histogram', 
                                            'Y offset in meters from static geo point', 
                                            buckets=GEO_BUCKETS_YX, registry=registry)
        metrics['GEO_OFFSET_X'] = Histogram('gpsd_geo_bearing_y_histogram', 
                                            'X offset in meters from static geo point', 
                                            buckets=GEO_BUCKETS_YX, registry=registry)


    metrics['registry'] = registry
        
    return(metrics)


def getPositionData(gpsd, metrics, args):
    try:
        # Check if gpsd object is still valid
        if not gpsd or not hasattr(gpsd, 'next'):
            log.error("GPSD connection object is invalid")
            raise ConnectionError("GPSD connection object is invalid")
            
        nx = gpsd.next()
    except KeyError as e:
        # Handle missing satellite data fields (like 'az', 'el', etc.)
        log.warning(f"GPSD reported incomplete satellite data: {e}")
        return
    except (ConnectionError, OSError, socket.error, BrokenPipeError, ConnectionResetError) as e:
        # Handle connection errors - re-raise to trigger retry
        log.error(f"Connection error reading from GPSD: {type(e).__name__}: {e}")
        raise
    except Exception as e:
        # Handle other GPSD connection or data parsing errors
        log.error(f"Error reading from GPSD: {type(e).__name__}: {e}")
        # For any other exception, assume it might be connection-related and re-raise
        # This is more aggressive but prevents the endless loop
        log.error(f"Re-raising unexpected error as connection error: {type(e).__name__}: {e}")
        raise ConnectionError(f"GPSD read error: {type(e).__name__}: {e}")
    
    # For a list of all supported classes and fields refer to:
    # https://gpsd.gitlab.io/gpsd/gpsd_json.html
    
    if (args.debug > 1): log.debug(f'recieved {nx["class"]}: {nx}') 
    
    if nx['class'] == 'VERSION':
        
        metrics['VERSION'].info({'release': nx['release'],
                     'rev': nx['rev'],
                     'proto_major': str(nx['proto_major']),
                     'proto_minor': str(nx['proto_minor']),
        })
    elif nx['class'] == 'PPS':
#         PPSSUMMARY.observe(nx['clock_nsec'])

        if args.pps:
            
            args.pps_time1
            corr = args.pps_time1 * NSEC
            value = nx['clock_nsec'] - corr
            
            if (value > (NSEC/2)):
                value = value - NSEC 
                
            log.debug (f"PPS offset {nx['clock_nsec']} -> {value}")
            log.debug(nx)
            
            metrics['PPS_HIS'].labels(nx['device']).observe(value)

    elif nx['class'] == 'DEVICES':
        for device in nx['devices']:
            log.debug(device)
        
            metrics['DEVICES'].labels(device['path']).info(
                {       
                    'driver': device['driver'] if 'driver' in device else "Unknown",
                    'subtype': device['subtype'] if 'subtype' in device else "Unknown",
                    'subtype1': device['subtype1'] if 'subtype1' in device else "Unknown",
                    'activated': device['activated'] if 'activated' in device else "Unknown",
                    'flags': str(device['flags']) if 'flags' in device else "Unknown",
                    'native': str(device['native']) if 'native' in device else "Unknown",
                    'bps': str(device['bps']) if 'bps' in device else "Unknown",
                    'parity': str(device['parity']) if 'parity' in device else "Unknown",
                    'stopbits': str(device['stopbits']) if 'stopbits' in device else "Unknown",
                    'cycle': str(device['cycle']) if 'cycle' in device else "Unknown",
                    'mincycle': str(device['mincycle']) if 'mincycle' in device else "Unknown",
            })
    
    elif nx['class'] == 'SKY':
        
        """process the list of satellites """
        satellites = nx.get('satellites')
        if satellites is None:
            log.debug (f'no satellites in SKY')
            log.debug (nx)
            return

        metrics['SEEN'].set(0)
        metrics['USED'].set(0)
            
        for sat in satellites:
            metrics['SEEN'].inc()
            if sat['used']:
                metrics['USED'].inc()
            
        if args.mon_satellites:
            add_sat_stats(satellites)        

        """process the dop metrics """
        for key in metrics['SKY'].keys():
            if (hasattr(nx, key)):

                value = getattr(nx, key, -1)
                metrics['SKY'][key].set(getattr(nx, key, -1))
                if (args.debug > 2): log.debug (f'set {key} to {value}') 


    elif nx['class'] == 'TPV':
        for key in metrics['TPV'].keys():
            if (hasattr(nx, key)):
                value = getattr(nx, key, -1)
                metrics['TPV'][key].set(value)
                if (args.debug > 2): log.debug (f'set {key} to {value}')
        
        if args.geo_offset:
            if (hasattr(nx, 'lat') and hasattr(nx, 'lon') ):
                offset = MeterOffsetSmall((args.geo_lat, args.geo_lon), (nx['lat'], nx['lon']))
                distance  = gps.misc.EarthDistanceSmall((nx['lat'], nx['lon']), (args.geo_lat, args.geo_lon))
                
                log.debug (f'distance {distance:0.2f}m offset x = {offset[0]:0.2f}m y = {offset[1]:0.2f}m')
                
                metrics['GEO_OFFSET_X'].observe(offset[0])
                metrics['GEO_OFFSET_Y'].observe(offset[1])
                metrics['GEO_OFFSET'].observe(distance)

    elif nx['class'] == 'WATCH':
        pass
    
    else:
        log.debug (f'received {nx["class"]}')
        log.debug (nx)

def MeterOffsetSmall(c1, c2):
    "Return offset in meters of second arg from first."
    (lat1, lon1) = c1
    (lat2, lon2) = c2
    dx = gps.misc.EarthDistanceSmall((lat1, lon1), (lat1, lon2))
    dy = gps.misc.EarthDistanceSmall((lat1, lon1), (lat2, lon1))
    if lat1 < lat2:
        dy = -dy
    if lon1 < lon2:
        dx = -dx
    return (dx, dy)

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return
 
    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid
 
    # Remove group privileges
    os.setgroups([])
 
    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)
 
    # Ensure a very conservative umask
    old_umask = os.umask(0o077)

def loop_connection(metrics, args):

    try:
        # Set socket timeout for the connection
        socket.setdefaulttimeout(args.timeout)
        
        log.info(f'Attempting to connect to gpsd at {args.hostname}:{args.port} with {args.timeout}s timeout')
        gpsd = gps.gps(host=args.hostname, port=args.port, verbose=1, mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE | gps.WATCH_SCALED)

        if not gpsd:
            log.critical(f'Could not connect to gpsd at {args.hostname}:{args.port}')
            raise ConnectionRefusedError(f'Failed to establish connection to gpsd at {args.hostname}:{args.port}')

        log.info(f'Successfully connected to gpsd at {args.hostname}:{args.port}')
        drop_privileges()
            
    except socket.timeout:
        log.critical(f'Connection to gpsd at {args.hostname}:{args.port} timed out after {args.timeout}s')
        raise ConnectionRefusedError(f'Connection timeout after {args.timeout}s')
    except ConnectionRefusedError:
        # Re-raise to be caught by the main loop
        raise
    except Exception as e:
        log.critical(f'Unexpected error connecting to gpsd: {e}')
        raise ConnectionRefusedError(f'Failed to connect to gpsd: {e}')
    running = True
    while running:
        try:
            getPositionData(gpsd, metrics, args)
        except KeyboardInterrupt:
            log.info("Received keyboard interrupt, shutting down...")
            raise
        except (ConnectionError, OSError, socket.error, BrokenPipeError, ConnectionResetError) as e:
            # Re-raise connection errors to trigger retry in main loop
            log.error(f"Connection error in data loop: {type(e).__name__}: {e}")
            raise
        except Exception as e:
            log.error(f"Unexpected error in main loop: {type(e).__name__}: {e}")
            # Continue running to avoid crashing the container
            continue

class SatCollector(object):
    
    
    def __init__(self):
        self.state = {}
    
    def collect(self):
        """
        This Method is called each time exporter is called to fetch the per Satellite metrics 
        """
        
        metrics = {
            'ss' : GaugeMetricFamily('gpsd_sat_ss', 'Signal to Noise ratio in dBHz.', labels=['PRN', 'svid', 'gnssid', 'used']),
            'az' : GaugeMetricFamily('gpsd_sat_az', 'Azimuth, degrees from true north.', labels=['PRN', 'svid', 'gnssid', 'used']),
            'el' : GaugeMetricFamily('gpsd_sat_el', 'Elevation in degrees.', labels=['PRN', 'svid', 'gnssid', 'used']),
            'used': GaugeMetricFamily('gpsd_used', 'Used Satellite', labels=['PRN', 'svid', 'gnssid', 'used']),
            'health' : GaugeMetricFamily('gpsd_health', 'The health of this satellite. 0 is unknown, 1 is OK, and 2 is unhealthy', labels=['PRN', 'svid', 'gnssid', 'used'])
        }
        
        log.debug(f'SatCollector::collect started ')
        last_measurement = {}
        
        while not sat_queue.empty():
            try:
                measurement = sat_queue.get()
                log.debug(f'measurement:: {measurement}')            

                sat = measurement['sat']
                ts = measurement['ts']
                
                last_measurement[sat['PRN']] = sat
            except KeyError as e:
                # Handle missing satellite data fields
                log.warning(f"Skipping satellite measurement due to missing field: {e}")
                continue
            except Exception as e:
                # Handle other satellite measurement processing errors
                log.error(f"Error processing satellite measurement: {e}")
                continue
            
        
        log.debug(f'last_measurement {last_measurement}')
            
        for sat in last_measurement.keys():
            log.debug(f'sat:: {last_measurement[sat]}')
            try:
                sat_dict = last_measurement[sat]

                # Extract label values with defaults for missing optional fields
                # PRN is required - will raise KeyError if missing
                prn = str(sat_dict['PRN'])
                # svid defaults to PRN for GPS-only receivers (semantically correct)
                svid = str(sat_dict.get('svid', sat_dict['PRN']))
                # gnssid defaults to 0 (GPS constellation per NMEA 0183) if missing
                gnssid = str(sat_dict.get('gnssid', 0))
                # used defaults to False if missing
                used = str(sat_dict.get('used', False))

                # Add all available metrics for this satellite
                for key in metrics.keys():
                    if key in sat_dict.keys():
                        metrics[key].add_metric([prn, svid, gnssid, used], sat_dict[key])

            except KeyError as e:
                # Only PRN is truly required - skip satellite if missing
                log.warning(f"Skipping satellite due to missing required field PRN: {e}")
                continue
            except Exception as e:
                # Handle other satellite metrics processing errors
                log.error(f"Error processing satellite metrics: {e}")
                continue 
                
        
        for key in metrics:
            yield metrics[key]
            

def add_sat_stats(satellites):
    
    for sat in satellites:
        try:
            ts = time.time()
            ts_new = int(ts)
            
            # print (f'ts {ts} ts_new {ts_new}' )
            
            sat_queue.put({'sat': sat, 'ts': ts})
        except KeyError as e:
            # Handle missing satellite data fields
            log.warning(f"Skipping satellite with missing data field: {e}")
            continue
        except Exception as e:
            # Handle other satellite data processing errors
            log.error(f"Error processing satellite data: {e}")
            continue
    
    """ Keep the queue managable. """
       
    q_size = sat_queue.qsize()
    log.debug(f'Queue size = {q_size} items.')
    while sat_queue.qsize() > 2000:
        sat_queue.get()

    q_size_end = sat_queue.qsize()
    log.debug(f'Current satellite queue size = {q_size_end}, pruned {q_size - q_size_end}')
    
if __name__ == "__main__":
        
    sys.exit(main())
    
