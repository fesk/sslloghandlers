# sslloghandlers
Python logging handlers that support SSL / HTTPS connections - one replacing HTTPHandler with a version that supports SSL and one providing a socket-based emitter that connects over SSL.

### HTTPHandler with SSL support - Use
*sslloghandler.HTTPHandler(host, url, method, secure, strict, json)*

*host* hostname:port

*url* path to send request to

*method* GET or POST (note if setting json to True then the request will always be a POST)

*secure* True|False - whether to use SSL/TLS

*strict* True|False - whether to perform certificate verification

*json* True|False - send as JSON or URL encoded.  If True, request will always be a POST


### HTTPHandler Example
```
import logging
from sslloghandler import HTTPHandler
logger = logging.getLogger('youlogger')
https_handler = HTTPHandler('localhost:4567', '/', secure=True, strict=False, json=True)
logger.addHandler(https_handler)
logger.info('meh')
```

You can create a local listener using (you'll need to create the self-signed cert and PEM file for this first);

```sh
$ openssl s_server -accept 4567 -cert /path/to/pemfile.pem
```

### SocketHandler with SSL support - Use
*sslloghandler.SocketHandler(host, secure, strict)*

*host* hostname:port

*secure* True|False - whether to use SSL/TLS

*strict* True|False - whether to perform certificate verification


### SocketHandler Example
```
import logging
from sslloghandler import SocketHandler
logger = logging.getLogger('youlogger')
sock_handler = SocketHandler('localhost:10080', strict=False)
logger.addHandler(sock_handler)
logger.info('meh')
```

You can create a local listener using (you'll need to create the self-signed cert and PEM file for this first);

```sh
$ openssl s_server -accept 10080 -cert /path/to/pemfile.pem
```

There is an example server implementation in logserver_example.py.



### Django Logging
To use this with Django logging configuration, you'll need to make sure sslloghandler is in your app or sys path.
Use the following in settings.py as an example LOGGING configuration;
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {

        'web': {
            'level': 'DEBUG',
            'class': 'sslloghandler.HTTPHandler',
            'host': 'localhost:4567',
            'url': '/',
            'method': 'POST',
            'secure': True,
            'strict': False,
            'json': True,
        },

        'sock': {
            'level': 'DEBUG',
            'class': 'sslloghandler.SocketHandler',
            'host': 'remotehost:10080',
            'strict': False,
        },

    },
    'loggers': {
        'django': {
            'handlers': ['web', 'sock'],
            'propagate': True,
            'level': 'INFO',
        },
    }
}
```

With this configuration, Django will then send all INFO or higher messages as JSON requests POSTed to your listening server over SSL/TLS (depending on config) and will also send them through the socket logger to remotehost:10080.


