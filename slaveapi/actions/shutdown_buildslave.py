from furl import furl
import requests
import time

from .results import SUCCESS, FAILURE
from ..clients.ping import ping
from ..clients.ssh import RemoteCommandError
from ..slave import Slave, get_console

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
    status_text = "Gracefully shutting down slave..."
    slave = Slave(name)
    slave.load_slavealloc_info()
    slave.load_devices_info()

    if not slave.master_url:
        status_text += "Success\nNo master set, nothing to do!"
        return SUCCESS, status_text

    if not ping(slave.fqdn):
        status_text += "Success\nSlave is offline, nothing to do!"
        return SUCCESS, status_text

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
        status_text += "Failure\nFailed to initiate graceful shutdown through %s" % (shutdown_url,)
        return FAILURE,  status_text

    twistd_log = "%s/%s" % (slave.basedir, "twistd.log")
    start = time.time()
    console = get_console(slave, usebuildbotslave=True)
    while console and time.time() - start < MAX_SHUTDOWN_WAIT_TIME:
        try:
            rc, output = console.run_cmd("tail -n1 %s" % twistd_log)
            if "Server Shut Down" in output:
                status_text += "Success"
                log.debug("%s - Shutdown succeeded." % slave.name)
                return SUCCESS, status_text
            else:
                time.sleep(30)
        except RemoteCommandError:
            log.debug("Caught error when waiting for shutdown, trying again...", exc_info=True)
            time.sleep(30)
    else:
        status_text += "Failure\nCouldn't confirm shutdown"
        return FAILURE, status_text
