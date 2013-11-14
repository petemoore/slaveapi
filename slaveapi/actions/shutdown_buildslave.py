from furl import furl
import requests
import time

from .results import SUCCESS, FAILURE
from ..slave import Slave, get_console, is_alive

import logging
log = logging.getLogger(__name__)

# The longest we will wait for a slave to shutdown.
MAX_SHUTDOWN_WAIT_TIME = 60 * 60 * 5 # 5 hours

def shutdown_buildslave(name):
    """Attempts to gracefully shut down the buildslave process on the named
    slave. In order to support Windows, this must be done by contacting the
    Buildbot Master the slave talks to, and requesting the shut down there.
    (Slave-side graceful shutdown doesn't work on Windows.) Once initiated,
    the shutdown is confirmed by watching the slave's twistd.log file."""
    slave = Slave(name)
    slave.load_slavealloc_info()

    # We do graceful shutdowns through the master's web interface because it's
    # the simplest way that works across all platforms.
    log.info("%s - Starting graceful shutdown.", slave.name)
    shutdown_url = furl(slave.master_url)
    shutdown_url.path = "/buildslaves/%s/shutdown" % slave.name
    try:
        # Disabling redirects is important here - otherwise we'll load a
        # potentially expensive page from the Buildbot master. The response
        # code is good enough to confirm whether or not initiating this worked
        # or not anyways.
        requests.post(str(shutdown_url), allow_redirects=False)
    except requests.RequestException:
        log.exception("%s - Failed to initiate graceful shutdown.", slave.name)
        return FAILURE, "%s - Failed to initiate graceful shutdown through %s" % (slave.name, shutdown_url)

    twistd_log = "%s/%s" % (slave.basedir, "twistd.log")
    start = time.time()
    console = get_console(slave)
    down = False
    while time.time() - start < MAX_SHUTDOWN_WAIT_TIME:
        try:
            rc, output = console.run_cmd("tail -n1 %s" % twistd_log)
            if "Server Shut Down" in output:
                down = True
                break
            else:
                time.sleep(30)
        except:
            log.debug("Caught error while waiting for graceful shutdown, checking to see if slave is still alive.", exc_info=True)
            if is_alive(slave, timeout=10):
                log.debug("Slave is still alive, trying again...")
                time.sleep(30)
            else:
                log.debug("Slave went down during graceful shutdown, assuming success.")
                down = True
                break

    if down:
        return SUCCESS, "Shutdown succeeded."
    else:
        return FAILURE, "Couldn't confirm shutdown."
