#!/usr/bin/python
"""
Python logging handlers support SSL connections to remote hosts.

Includes socket-server based handler and replacement HTTPHandler, both supporting SSL.

Nick Besant 2017 hwf@fesk.net

"""
import logging
import socket
import ssl
import httplib
import urllib
import json
from time import time


class SocketHandler(logging.Handler):
    """
     Sends log records to a socket-based log handler, supporting SSL/TLS connections.

     Args:
        host: hostname:port - if no port is provided, a default of 10800 is used
        secure: True|False - whether to use SSL/TLS
        strict: True|False - whether to perform certificate verification
        path: string with additional path data (e.g. source file path / source URL etc.)

    Derived from hwf@fesk.net's HTTPHandler

    hwf@fesk.net 2017

    """
    def __init__(self, host, secure=True, strict=True, path=None):
        """
        Initialize the instance with the host, the request URL and whether to perform certificate verification (strict).
        """
        logging.Handler.__init__(self)

        if ':' in host:
            self.host = host.split(':')[0]
            self.port = int(host.split(':')[1])
        else:
            self.host = host
            self.port = 10800
        if path:
            self.path = path
        else:
            self.path = ''
        self.dosecure = secure
        self.strict = strict

    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent as the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """
        return record.__dict__

    def emit(self, record):
        """
        Emit a record.

        Sends the record to the log host.
        """
        try:

            r_data = self.mapLogRecord(record)
            data_msg = r_data.get('msg', u'-')
            if type(data_msg) == list:
                data_msg = u' '.join(data_msg)
            else:
                try:
                    data_msg = data_msg.__str__()
                except:
                    data_msg = type(data_msg)
                    pass

            s_data = u'%s|%s|%s|%s|%s|%s' % (r_data.get('created', time()),
                                             socket.gethostname(),
                                             self.path,
                                             r_data.get('name', u'-'),
                                             r_data.get('levelname', u'INFO'),
                                             data_msg.replace(u'|', u'\|'),
                                             )

            try:
                if self.dosecure:
                    plainsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    if self.strict:
                        certreq = ssl.CERT_REQUIRED
                    else:
                        certreq = ssl.CERT_NONE
                    connsock = ssl.wrap_socket(plainsock,
                                               cert_reqs=certreq,
                                               ssl_version=ssl.PROTOCOL_TLSv1_2)
                    connsock.connect((self.host, int(self.port)))
                    connsock.write(s_data)
                    connsock.close()

                else:
                    connsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    connsock.connect((self.host, int(self.port)))
                    connsock.send(s_data)
                    connsock.close()
            except socket.error as e:
                if e.errno == 111:
                    print 'TCP logger: message from {0} - connection ' \
                          'to {1}:{2} {3}refused'.format(r_data.get('name', u'-'),
                                                         self.host,
                                                         self.port,
                                                         'over SSL ' if self.dosecure else '')
                else:
                    raise

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class HTTPHandler(logging.Handler):
    """
     A class which sends records to a Web server, using either GET or
     POST semantics, supporting SSL/TLS connections and sending data either as a URL-encoded value or as
     a JSON body.

     Args:
        host: hostname:port
        url: path to send request to
        method: GET or POST (note if setting json to True then the request will always be a POST)
        secure: True|False - whether to use SSL/TLS
        strict: True|False - whether to perform certificate verification
        json: True|False - send as JSON or URL encoded.  If True, request will always be a POST

     See https://docs.python.org/2/library/logging.handlers.html for more information about the HTTPHandler
     and its mapLogRecord and emit methods.

    Derived from python standard logging.handlers.HTTPHandler

    hwf@fesk.net 2016

    """
    def __init__(self, host, url, method="GET", secure=True, strict=True, json=True):
        """
        Initialize the instance with the host, the request URL, the method
        ("GET" or "POST"), whether to perform certificate verification (strict) and whether to send
        as a POSTed JSON request.
        """
        logging.Handler.__init__(self)
        method = method.upper()
        if method not in ["GET", "POST"]:
            raise ValueError("method must be GET or POST")

        if ':' in host:
            self.host = host.split(':')[0]
            self.port = int(host.split(':')[1])
        else:
            self.host = host
            self.port = 443 if secure else 80
        self.url = url
        self.method = 'POST' if json else method
        self.dosecure = secure
        self.strict = strict
        self.json = json

    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent as the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """
        return record.__dict__

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Web server as a percent-encoded dictionary or as JSON
        """
        try:

            host = self.host
            if self.dosecure:
                if self.strict:
                    h = httplib.HTTPSConnection(host, self.port)
                else:
                    h = httplib.HTTPSConnection(host, port=self.port, context=ssl._create_unverified_context())
            else:
                h = httplib.HTTP(host)
            url = self.url
            if self.json:
                content_type = 'application/json'
                data = json.dumps(self.mapLogRecord(record))
            else:
                content_type = 'application/x-www-form-urlencoded'
                data = urllib.urlencode(self.mapLogRecord(record))
            if self.method == "GET":
                if (url.find('?') >= 0):
                    sep = '&'
                else:
                    sep = '?'
                url = url + "%c%s" % (sep, data)
            h.putrequest(self.method, url)
            # support multiple hosts on one IP address...
            # need to strip optional :port from host, if present
            i = host.find(":")
            if i >= 0:
                host = host[:i]
            h.putheader("Host", host)
            if self.method == "POST":
                h.putheader("Content-type",
                            content_type)
                h.putheader("Content-length", str(len(data)))
            h.endheaders(data if self.method == "POST" else None)
            h.getreply()    #can't do anything with the result
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

