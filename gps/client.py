# This file is Copyright 2019 by the GPSD project
# SPDX-License-Identifier: BSD-2-Clause
#
# This code run compatibly under Python 2 and 3.x for x >= 2.
# Preserve this property!
# Codacy D203 and D211 conflict, I choose D203
# Codacy D212 and D213 conflict, I choose D212


"""gpsd client functions."""

from __future__ import absolute_import, print_function, division

import json
import select
import socket
import sys
import time

import gps          # for VERB_*
from .misc import polystr, polybytes
from .watch_options import *

GPSD_PORT = "2947"


class gpscommon(object):

    """Isolate socket handling and buffering from protocol interpretation."""
    host = "127.0.0.1"
    port = GPSD_PORT

    def __init__(self,
                 device=None,
                 host="127.0.0.1",
                 input_file_name=None,
                 port=GPSD_PORT,
                 should_reconnect=False,
                 verbose=0):
        """Init gpscommon."""
        self.device = device
        self.input_file_name = input_file_name
        self.input_fd = None
        self.linebuffer = b''
        self.received = time.time()
        self.reconnect = should_reconnect
        self.sock = None        # in case we blow up in connect
        self.stream_command = b''
        self.verbose = verbose
        # Provide the response in both 'str' and 'bytes' form
        self.bresponse = b''
        self.response = polystr(self.bresponse)

        if gps.VERB_PROG <= verbose:
            print('gpscommon(device=%s host=%s port=%s\n'
                  '          input_file_name=%s verbose=%s)' %
                  (device, host, port, input_file_name, verbose))

        if input_file_name:
            # file input, binary mode, for binary data.
            self.input_fd = open(input_file_name, "rb")

        elif host is not None and port is not None:
            self.host = host
            self.port = port
            self.connect(self.host, self.port)
        # else?

    def connect(self, host, port):
        """Connect to a host on a given port.

        If the hostname ends with a colon (`:') followed by a number, and
        there is no port specified, that suffix will be stripped off and the
        number interpreted as the port number to use.
        """
        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if 0 <= i:
                host, port = host[:i], host[i + 1:]
            try:
                port = int(port)
            except ValueError:
                raise socket.error("nonnumeric port")
        # if 0 < self.verbose:
        #    print 'connect:', (host, port)
        self.sock = None
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, _canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                # if 0 < self.debuglevel: print 'connect:', (host, port)
                self.sock.connect(sa)
                if 0 < self.verbose:
                    print('connected to tcp://{}:{}'.format(host, port))
                break
            # do not use except ConnectionRefusedError
            # # Python 2.7 doc does have this exception
            except socket.error as e:
                if 1 < self.verbose:
                    msg = str(e) + ' (to {}:{})'.format(host, port)
                    sys.stderr.write("error: {}\n".format(msg.strip()))
                self.close()
                raise  # propagate error to caller

    def close(self):
        """Close the gpsd socket or file."""
        if self.input_fd:
            self.input_fd.close()
        self.input_fd = None
        if self.sock:
            self.sock.close()
        self.sock = None

    def __del__(self):
        """Close the gpsd socket."""
        self.close()

    def waiting(self, timeout=0):
        """Return True if data is ready for the client."""
        if self.linebuffer or self.input_fd:
            # check for input_fd EOF?
            return True
        if self.sock is None:
            return False

        (winput, _woutput, _wexceptions) = select.select(
            (self.sock,), (), (), timeout)
        return [] != winput

    def read(self):
        """Wait for and read data being streamed from the daemon."""
        if not self.input_fd and None is self.sock:
            # input_fd.open() was earlier, and read_only, so no stream()
            self.connect(self.host, self.port)
            if None is self.sock:
                return -1
            self.stream()

        eol = self.linebuffer.find(b'\n')
        if -1 == eol:
            # RTCM3 JSON can be over 4.4k long, so go big
            if self.input_fd:
                frag = self.input_fd.read(8192)
            else:
                frag = self.sock.recv(8192)

            if not frag:
                if 1 < self.verbose:
                    sys.stderr.write(
                        "poll: no available data: returning -1.\n")
                # Read failed
                return -1

            self.linebuffer += frag

            eol = self.linebuffer.find(b'\n')
            if -1 == eol:
                if 1 < self.verbose:
                    sys.stderr.write("poll: partial message: returning 0.\n")
                # Read succeeded, but only got a fragment
                self.response = ''  # Don't duplicate last response
                self.bresponse = b''  # Don't duplicate last response
                return 0
        else:
            if 1 < self.verbose:
                sys.stderr.write("poll: fetching from buffer.\n")

        # We got a line
        eol += 1
        # Provide the response in both 'str' and 'bytes' form
        self.bresponse = self.linebuffer[:eol]
        self.response = polystr(self.bresponse)
        self.linebuffer = self.linebuffer[eol:]

        # Can happen if daemon terminates while we're reading.
        if not self.response:
            return -1
        if 1 < self.verbose:
            sys.stderr.write("poll: data is %s\n" % repr(self.response))
        self.received = time.time()
        # We got a \n-terminated line
        return len(self.response)

    # Note that the 'data' method is sometimes shadowed by a name
    # collision, rendering it unusable.  The documentation recommends
    # accessing 'response' directly.  Consequently, no accessor method
    # for 'bresponse' is currently provided.

    def data(self):
        """Return the client data buffer."""
        return self.response

    def send(self, commands):
        """Ship commands to the daemon."""
        lineend = "\n"
        if isinstance(commands, bytes):
            lineend = polybytes("\n")
        if not commands.endswith(lineend):
            commands += lineend

        if self.sock is None:
            self.stream_command = commands
        else:
            self.sock.send(polybytes(commands))


class json_error(BaseException):

    """Class for JSON errors."""

    def __init__(self, data, explanation):
        """Init json_error."""
        BaseException.__init__(self)
        self.data = data
        self.explanation = explanation


class gpsjson(object):

    """Basic JSON decoding."""

    def __init__(self, verbose=0):
        """Init gpsjson."""
        self.data = None
        self.stream_command = None
        self.enqueued = None
        self.verbose = verbose

    def __iter__(self):
        """Broken __iter__."""
        return self

    def unpack(self, buf):
        """Unpack a JSON string."""
        try:
            # json.loads(,encoding=) deprecated Python 3.1.  Gone in 3.9
            # like it or not, data is now UTF-8
            self.data = dictwrapper(json.loads(buf.strip()))
        except ValueError as e:
            raise json_error(buf, e.args[0])
        # Should be done for any other array-valued subobjects, too.
        # This particular logic can fire on SKY or RTCM2 objects.
        if hasattr(self.data, "satellites"):
            self.data.satellites = [dictwrapper(x)
                                    for x in self.data.satellites]

    def stream(self, flags=0, devpath=None):
        """Control streaming reports from the daemon,"""
        if 0 < flags:
            self.stream_command = self.generate_stream_command(flags, devpath)
        else:
            self.stream_command = self.enqueued

        if self.stream_command:
            if 1 < self.verbose:
                sys.stderr.write("send: stream as:"
                                 " {}\n".format(self.stream_command))
            self.send(self.stream_command)
        else:
            raise TypeError("Invalid streaming command!! : " + str(flags))

    def generate_stream_command(self, flags=0, devpath=None):
        """Generate stream command."""
        if flags & WATCH_OLDSTYLE:
            return self.generate_stream_command_old_style(flags)

        return self.generate_stream_command_new_style(flags, devpath)

    @staticmethod
    def generate_stream_command_old_style(flags=0):
        """Generate stream command, old style."""
        if flags & WATCH_DISABLE:
            arg = "w-"
            if flags & WATCH_NMEA:
                arg += 'r-'

        elif flags & WATCH_ENABLE:
            arg = 'w+'
            if flags & WATCH_NMEA:
                arg += 'r+'

        return arg

    @staticmethod
    def generate_stream_command_new_style(flags=0, devpath=None):
        """Generate stream command, new style."""
        if (flags & (WATCH_JSON | WATCH_OLDSTYLE | WATCH_NMEA |
                     WATCH_RAW)) == 0:
            flags |= WATCH_JSON

        if flags & WATCH_DISABLE:
            arg = '?WATCH={"enable":false'
            if flags & WATCH_JSON:
                arg += ',"json":false'
            if flags & WATCH_NMEA:
                arg += ',"nmea":false'
            if flags & WATCH_RARE:
                arg += ',"raw":1'
            if flags & WATCH_RAW:
                arg += ',"raw":2'
            if flags & WATCH_SCALED:
                arg += ',"scaled":false'
            if flags & WATCH_TIMING:
                arg += ',"timing":false'
            if flags & WATCH_SPLIT24:
                arg += ',"split24":false'
            if flags & WATCH_PPS:
                arg += ',"pps":false'
        else:  # flags & WATCH_ENABLE:
            arg = '?WATCH={"enable":true'
            if flags & WATCH_JSON:
                arg += ',"json":true'
            if flags & WATCH_NMEA:
                arg += ',"nmea":true'
            if flags & WATCH_RARE:
                arg += ',"raw":1'
            if flags & WATCH_RAW:
                arg += ',"raw":2'
            if flags & WATCH_SCALED:
                arg += ',"scaled":true'
            if flags & WATCH_TIMING:
                arg += ',"timing":true'
            if flags & WATCH_SPLIT24:
                arg += ',"split24":true'
            if flags & WATCH_PPS:
                arg += ',"pps":true'
            if flags & WATCH_DEVICE:
                arg += ',"device":"%s"' % devpath
        arg += "}"
        return arg


class dictwrapper(object):

    """Wrapper that yields both class and dictionary behavior,"""

    def __init__(self, ddict):
        """Init class dictwrapper."""
        self.__dict__ = ddict

    def get(self, k, d=None):
        """Get dictwrapper."""
        return self.__dict__.get(k, d)

    def keys(self):
        """Keys dictwrapper."""
        return self.__dict__.keys()

    def __getitem__(self, key):
        """Emulate dictionary, for new-style interface."""
        return self.__dict__[key]

    def __iter__(self):
        """Iterate dictwrapper."""
        return self.__dict__.__iter__()

    def __setitem__(self, key, val):
        """Emulate dictionary, for new-style interface."""
        self.__dict__[key] = val

    def __contains__(self, key):
        """Find key in dictwrapper."""
        return key in self.__dict__

    def __str__(self):
        """dictwrapper to string."""
        return "<dictwrapper: " + str(self.__dict__) + ">"
    __repr__ = __str__

    def __len__(self):
        """length of dictwrapper."""
        return len(self.__dict__)

#
# Someday a cleaner Python interface using this machinery will live here
#

# End
# vim: set expandtab shiftwidth=4
