#!/usr/bin/python
"""
Example socket server implementation for receiving log message data over
SSL - e.g. from SocketHandler in sslloghandlers

Nick Besant 2017 hwf@fesk.net

"""

import ssl
from SocketServer import TCPServer, ThreadingMixIn, StreamRequestHandler


class LoggingRequestHandler(StreamRequestHandler):
    """Example implementation for logging handler (see SocketHandler class)"""

    def handle(self):
        """Replace this with your own code to do something with the log messages we receive."""

        # Get the data (just the first chunk / line as a line from the file object) sent to us
        data = self.rfile.readline().strip()

        print data


class ThreadedServer(ThreadingMixIn, TCPServer):
    """Thread server stub."""

    def get_request(self):
        """Override get_request to call do_handshake so that we're non-blocking."""

        (socket, addr) = TCPServer.get_request(self)
        socket.do_handshake()
        return (socket, addr)


ip_to_serve = '127.0.0.1'
port_choice = 10800

print '\n\nListening on {0}:{1}\n'.format(ip_to_serve, port_choice)

tcpd = ThreadedServer((ip_to_serve, port_choice), LoggingRequestHandler)
tcpd.socket = ssl.wrap_socket(tcpd.socket,
                              keyfile="default.key",
                              certfile="default.cert",
                              server_side=True,
                              do_handshake_on_connect=False,
                              ssl_version=ssl.PROTOCOL_TLSv1_2)
tcpd.serve_forever()
