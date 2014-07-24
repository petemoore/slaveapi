#!/usr/bin/env python

"""SlaveAPI Server.

Usage:
  slaveapi-server.py start (<config_file>)
  slaveapi-server.py stop (<config_file>)
  slaveapi-server.py reload (<config_file>)
"""

# Gevent patching needs to be done before importing anything else.
from gevent import monkey
monkey.patch_all()
import gevent, gevent.core
from gevent import pywsgi, socket
from gevent.event import Event

# Semaphore is in gevent.lock for gevent >= 1.0, coros is deprecated but available
from gevent.coros import Semaphore

# Need to patch subprocess by hand, because it's provided by a different module
import gevent_subprocess
import subprocess
for patch in ("Popen", "call", "check_call", "check_output"):
    patched = getattr(gevent_subprocess, patch)
    setattr(subprocess, patch, patched)

from ConfigParser import RawConfigParser, NoOptionError
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from signal import SIGHUP, SIGINT
from socket import SOL_SOCKET, SO_REUSEADDR
import sys

import daemon
from daemon.daemon import get_maximum_file_descriptors

from slaveapi.global_state import bugzilla_client, config, processor, messenger
from slaveapi.global_state import semaphores, log_data
from slaveapi.web import app
from slaveapi.util import logException

log = logging.getLogger(__name__)


class logger(object):
    def write(self, msg):
        log.info(msg)


def slashify(url):
    if not url.endswith("/"):
        url += "/"
    return url

def load_config(ini):
    config["concurrency"] = ini.getint("server", "concurrency")
    # Trailing slashes are important on URLs because urljoin sucks.
    config["slavealloc_api_url"] = slashify(ini.get("slavealloc", "api_url"))
    config["inventory_api_url"] = slashify(ini.get("inventory", "api_url"))
    config["inventory_username"] = ini.get("inventory", "username")
    config["bugzilla_api_url"] = slashify(ini.get("bugzilla", "api_url"))
    config["bugzilla_username"] = ini.get("bugzilla", "username")
    config["buildapi_api_url"] = slashify(ini.get("buildapi", "api_url"))
    config["default_domain"] = ini.get("slaves", "default_domain")
    config["ipmi_username"] = ini.get("slaves", "ipmi_username")
    config["devices_json_url"] = ini.get("devices", "devices_json_url")

def load_credentials(credentials):
    config["ssh_credentials"] = credentials["ssh"]
    config["inventory_password"] = credentials["inventory"]
    config["bugzilla_password"] = credentials["bugzilla"]
    config["ipmi_password"] = credentials["ipmi"]

def setup_logging(level, logfile=None, maxsize=None, maxfiles=None):
    # Quiet down some of the libraries that we use.
    logging.getLogger("paramiko").setLevel(logging.WARN)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("bzrest").setLevel(logging.INFO)

    if logfile:
        handler = RotatingFileHandler(logfile, maxBytes=maxsize, backupCount=maxfiles)
    else:
        handler = logging.StreamHandler()
        
    class SlaveLogFilter(logging.Filter):
        def filter(self, record):
            record.slave = getattr(log_data, "slave", "-=-")
            return True

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(slave)s - %(message)s")
    handler.addFilter(SlaveLogFilter())
    handler.setFormatter(fmt)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

def run(config_file):
    log.info("Running with pid %i", os.getpid())
    server = None
    listener = None
    handler = None

    cached_sem_max = {"buildapi": 0}

    while True:
        # Despite our caller already opening and reading this, we need to do it
        # here to make sure we pick up any changes during a reload.
        ini = RawConfigParser()
        ini.read(args["<config_file>"])
        load_config(ini)

        credentials_file = ini.get("secrets", "credentials_file")
        credentials = json.load(open(credentials_file))
        load_credentials(credentials)
        # TODO: test credentials at startup

        # Setup max concurrency for buildapi
        max_buildapi = int(ini.get("buildapi", "max_concurrent"))
        if "buildapi" not in semaphores:
            semaphores["buildapi"] = Semaphore(max_buildapi)
        else:
            if max_buildapi != cached_sem_max["buildapi"]:
                semaphores["buildapi"].counter += max_buildapi - cached_sem_max["buildapi"]
        cached_sem_max["buildapi"] = max_buildapi

        listen = ini.get("server", "listen")
        port = ini.getint("server", "port")

        bugzilla_client.configure(
            config["bugzilla_api_url"],
            config["bugzilla_username"],
            config["bugzilla_password"],
        )
        processor.configure(config["concurrency"])
        gevent.spawn(messenger)

        if not listener or (listen, port) != listener.getsockname():
            if listener and server:
                log.info("Listener has changed, stopping old server")
                log.debug("Old address: %s", listener.getsockname())
                log.debug("New address: %s", (listen, port))
                server.stop()
            listener = socket.socket()
            listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            listener.bind((listen, port))
            listener.listen(256)

        server = pywsgi.WSGIServer(listener, app, log=logger())

        sighup_event = Event()
        h = gevent.signal(SIGHUP, lambda e: e.set(), sighup_event)
        if handler:
            handler.cancel()
        handler = h
        log.info("Running at %s", repr(server))
        try:
            gevent.spawn(server.serve_forever)
            sighup_event.wait()
        except KeyboardInterrupt:
            break
    log.info("pid %i exited normally", os.getpid())


if __name__ == "__main__":
    from docopt import docopt
    args = docopt(__doc__)

    config_ini = RawConfigParser()
    config_ini.read(args["<config_file>"])
    pidfile = config_ini.get("server", "pidfile")

    if args["stop"]:
        try:
            pid = int(open(pidfile).read())
            os.kill(pid, SIGINT)
        except (IOError, ValueError):
            log.info("No pidfile, assuming process is stopped.")
        sys.exit(0)
    elif args["reload"]:
        pid = int(open(pidfile).read())
        os.kill(pid, SIGHUP)
        sys.exit(0)
    elif args["start"]:
        daemonize = config_ini.getboolean("server", "daemonize")
        loglevel = config_ini.get("logging", "level")
        try:
            logfile = os.path.abspath(config_ini.get("logging", "file"))
        except NoOptionError:
            logfile = None
        if logfile:
            logsize = config_ini.getint("logging", "maxsize")
            log_maxfiles = config_ini.getint("logging", "maxfiles")
        else:
            logsize = None
            log_maxfiles = None
        setup_logging(loglevel, logfile, logsize, log_maxfiles)

        curdir = os.path.abspath(os.curdir)
        if daemonize:
            # Gevent 0.13 + daemonization breaks DNS resolution (https://github.com/surfly/gevent/issues/2)
            # A workaround for this is to not close the open file descriptors
            # when daemonizing.
            maxfd = get_maximum_file_descriptors()
            daemon_ctx = daemon.DaemonContext(signal_map={}, working_directory=curdir, umask=0o077, files_preserve=range(maxfd+2))
            daemon_ctx.open()

            gevent.reinit()
            open(pidfile, "w").write(str(os.getpid()))

        try:
            run(args["<config_file>"])
        except:
            logException(log.error, "Couldn't run server.")
            raise
        finally:
            try:
                if daemonize:
                    daemon_ctx.close()
                try:
                    os.unlink(pidfile)
                except OSError, e:
                    if e.errno == 2:
                        pass
                    else:
                        raise
                log.info("Exiting")
            except:
                logException(log.error, "Error shutting down.")
