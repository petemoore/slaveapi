import logging
import socket

import gevent
from gevent import pywsgi
from gevent.event import Event

from slaveapi import config, bugzilla_client, secrets
from slaveapi.server import SlaveAPIWSGIApp

# Trailing slashes are important because urljoin sucks!
config["slavealloc_api"] = "http://slavealloc.build.mozilla.org/api/"
config["inventory_api"] = "https://inventory.mozilla.org/en-US/tasty/v3/"
config["bugzilla_api"] = "https://bugzilla-dev.allizom.org/xmlrpc.cgi"
config["bugzilla_product"] = "mozilla.org"
config["bugzilla_component"] = "Release Engineering: Machine Management"
config["bugzilla_username"] = "bhearsum@mozilla.com"

bugzilla_client.configure(config["bugzilla_api"])
bugzilla_client.login(config["bugzilla_username"], secrets.bugzilla_password)

app = SlaveAPIWSGIApp()
listener = gevent.socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", 9999))
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
