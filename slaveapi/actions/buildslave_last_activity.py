from furl import furl
import requests
import time
import re
import dateutil.parser
from datetime import datetime

from .results import SUCCESS, FAILURE
from ..clients.ping import ping
from ..clients.ssh import RemoteCommandError
from ..slave import Slave, get_console
from ..actions.buildslave_uptime import buildslave_uptime

import logging
log = logging.getLogger(__name__)


def buildslave_last_activity(name):
    """Get the build slave state, last activity time, and uptime.
    Returns a dictionary of the form:
    {
        'last_state': # unknown, booting, stopped, ready, running_command
        'last_activity_seconds': # last activity age according to twistd.log, in seconds.
        'uptime': uptime # machine uptime, in seconds.
    }
    """
    slave = Slave(name)
    slave.load_slavealloc_info()
    slave.load_devices_info()

    rc, uptime = buildslave_uptime(name)
    if rc != SUCCESS:
        return rc, uptime
    cur_time = time.time()

    if uptime < 3 * 60:
        # Assume we're still booting
        log.debug("uptime is %.2f; assuming we're still booting up", uptime)
        return SUCCESS, { "state": "booting", "last_activity": 0 }

    console = get_console(slave, usebuildbotslave=False)
    try:
        log.debug("tailing twistd.log")
        log.debug("slave.basedir='%s'" % slave.basedir)
        # we'll disregard the return code b/c it will be non-zero if twistd.log.1 is not found
        rc, output = console.run_cmd("tail -n 100 %(basedir)s/twistd.log.1 %(basedir)s/twistd.log" % { 'basedir': slave.basedir })
    except RemoteCommandError:
        return FAILURE, "failed to tail twistd.log"
    console.disconnect()

    # account for the time it took to retrieve the log tail
    # and reset cur_time
    uptime = uptime + int(time.time() - cur_time)
    cur_time = time.time()

    last_activity = None
    running_command = False
    line = ""
    last_activity = cur_time
    last_state = "unknown"
    for line in output.splitlines():
        time.sleep(0)
        m = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            last_activity = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        else:
            # Not sure what to do with this line...
            continue

        if "RunProcess._startCommand" in line or "using PTY: " in line:
            log.debug("started command - %s", line.strip())
            running_command = True
        elif "commandComplete" in line or "stopCommand" in line:
            log.debug("done command - %s", line.strip())
            running_command = False

        if "Shut Down" in line:
            # Check if this happened before we booted, i.e. we're still booting up
            if (cur_time - last_activity) > uptime:
                log.debug(
                    "last activity delta (%s) is older than uptime (%s); assuming we're still booting %s",
                    (last_activity - cur_time), uptime, line.strip())
                last_state = "booting"
            else:
                last_state = "stopped"
        elif "I have a leftover directory" in line:
            # Ignore this, it doesn't indicate anything
            continue
        elif "slave is ready" in line:
            if (cur_time - last_activity) < uptime:
                last_state = "ready"
        elif running_command:
            # We're in the middle of running something
            last_state = "running_command"
            # Reset last_activity to "now"
            last_activity = cur_time

    return SUCCESS, {
        'last_state': last_state,
        'last_activity_seconds': (cur_time - last_activity),
        'uptime': uptime,
    }

