import logging
import signal
import socket

import gevent
from gevent import pywsgi
from gevent.event import Event

from slaveapi.server import SlaveAPIWSGIApp

app = SlaveAPIWSGIApp()
listener = gevent.socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(('127.0.0.1', 9999))
listener.listen(256)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

class logger(object):
    def write(self, msg):
        log.info(msg)

server = pywsgi.WSGIServer(listener, app, log=logger())

sighup_event = Event()
gevent.spawn(server.serve_forever)
sighup_event.wait()
