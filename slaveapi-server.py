import logging
import socket

import gevent
from gevent import monkey, pywsgi
from gevent.event import Event

# Make ALL the things non-blocking.
monkey.patch_all()

from slaveapi import bugzilla_client, config
from slaveapi.server import SlaveAPIWSGIApp

# Trailing slashes are important because urljoin sucks!
config["slavealloc_api"] = "http://slavealloc.build.mozilla.org/api/"
config["inventory_api"] = "https://inventory.mozilla.org/en-US/tasty/v3/"
config["inventory_username"] = "bhearsum@mozilla.com"
config["bugzilla_api"] = "https://bugzilla-dev.allizom.org/rest/"
config["bugzilla_product"] = "mozilla.org"
config["bugzilla_component"] = "Release Engineering: Machine Management"
config["bugzilla_username"] = "bhearsum@mozilla.com"
config["default_domain"] = "build.mozilla.org"
config["ssh_credentials_file"] = "credentials.json"

import json
from getpass import getpass
# TODO: test credentials at startup
config["ssh_credentials"] = json.load(open(config["ssh_credentials_file"]))
config["inventory_password"] = getpass("Inventory password: ")
config["bugzilla_password"] = getpass("Bugzilla password: ")
bugzilla_client.configure(
    config["bugzilla_api"],
    config["bugzilla_username"],
    config["bugzilla_password"],
)

app = SlaveAPIWSGIApp()
listener = gevent.socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", 9999))
listener.listen(256)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
logging.getLogger("paramiko").setLevel(logging.WARN)
logging.getLogger("requests").setLevel(logging.WARN)

class logger(object):
    def write(self, msg):
        log.info(msg)

server = pywsgi.WSGIServer(listener, app, log=logger())

sighup_event = Event()
gevent.spawn(server.serve_forever)
sighup_event.wait()
