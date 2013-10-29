import time

from .results import SUCCESS, FAILURE
from ..slave import Slave, get_console

import logging
log = logging.getLogger(__name__)

def shutdown_buildslave(name, graceful=True):
    """Attempts to shutdown the buildslave process on the named slave. If
    graceful is True, a graceful shutdown will be used. If False, the process
    will be killed immediately."""
    slave = Slave(name)
    slave.load_slavealloc_info()
    console = get_console(slave)

    if graceful:
        return graceful_shutdown(slave, console)
    else:
        return forced_shutdown(slave, console)

def graceful_shutdown(slave, console):
    log.info("%s - Attempting graceful shutdown of buildslave.", slave.name)
    # XXX: does this work with windows slaves?
    shutdown_file = "%s/%s" % (slave.basedir, "shutdown.stamp")
    twistd_log = "%s/%s" % (slave.basedir, "twistd.log")
    rc, output = console.run_cmd("touch %s" % shutdown_file)
    if rc != 0:
        return FAILURE, "Shutdown failed: %s" % output
    else:
        # It will take a short amount of time for Buildbot to recognize the
        # shutdown request. The output of twistd.log will indicate if the
        # slave shuts down.
        for _ in range(5):
            rc, output = console.run_cmd("tail -n1 %s" % twistd_log)
            if "Server Shut Down" in output:
                return SUCCESS, "Shutdown succeeded."
            else:
                time.sleep(5)
        else:
            return FAILURE, "Couldn't confirm shutdown."

def forced_shutdown(slave, console):
    log.info("%s - Attempting forceful shutdown of buildslave.", slave.name)
    rc, output = console.run_cmd("buildslave stop %s" % slave.basedir)
    log.debug(output)
    if rc != 0:
        return FAILURE, "Shutdown failed: %s" % output
    else:
        return SUCCESS, "Shutdown succeeded."
