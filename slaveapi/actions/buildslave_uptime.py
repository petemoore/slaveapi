from furl import furl
import requests
import time

from .results import SUCCESS, FAILURE
from ..clients.ping import ping
from ..clients.ssh import RemoteCommandError
from ..slave import Slave, get_console

import logging
log = logging.getLogger(__name__)


import re
import dateutil.parser
from datetime import datetime


def get_windows_uptime(cmd_text):
    """Parse the output from `net statistics server` and
    return the length of time in seconds the server has been up.
    """
    for line in cmd_text.splitlines():
        # looking for something like:
        # Statistics since 3/26/2014 7:14:07 AM
        match = re.match('Statistics since (.+)', line)
        if match:
            _timedelta = datetime.today() - dateutil.parser.parse(match.group(1))
            return int(_timedelta.total_seconds())
    return None


def get_unix_uptime(cmd_text):
    """Parse the output from UNIX `uptime` and return the
    length of time in seconds the server has been up.
    """
    for line in cmd_text.splitlines():
        # look for something resembling one of these:
        # 10:38:58 up 78 days, 21:57,  3 users,  load average: 0.01, 0.07, 0.13
        # 10:37  up 1 day, 12:02, 7 users, load averages: 0.62 0.47 0.45
        # 07:38:12 up 33 min,  1 user,  load average: 4.26, 4.24, 3.51
        # 08:18:28 up 0 min,  2 users,  load average: 1.52, 0.40, 0.13
        # 10:18:11 up  2:00,  2 users,  load average: 0.07, 0.02, 0.00
        up_seconds = None
        match = re.search('up\s+(\d+)\s+(\w+)(?:,\s+(\d{1,2}):(\d{2}))?', line)
        if match:
            m1 = int(match.group(1))
            m1_unit = match.group(2)
            hh = mm = None
            if len(match.groups()) > 2:
                hh = match.group(3)
                mm = match.group(4)
            to_seconds = {
                'day': 60 * 60 * 24,
                'days': 60 * 60 * 24,
                'min': 60,
            }
            up_seconds = m1 * to_seconds[m1_unit]
            if hh and mm:
                up_seconds = up_seconds + int(hh) * 60 * 60 + int(mm) * 60
        else:
            match = re.search('up\s+(\d{1,2}):(\d{2})', line)
            if match:
                hh = match.group(1)
                mm = match.group(2)
                up_seconds = int(hh) * 60 * 60 + int(mm) * 60
        if up_seconds is not None:
            return(up_seconds)


def buildslave_uptime(name):
    """Attempts to retrieve the build slave uptime (time since last reboot).
    This is done with the "uptime" command on Unix-based OS's, and
    by running "net statistics server" on windows.
    """
    slave = Slave(name)
    slave.load_slavealloc_info()
    slave.load_devices_info()

    if not ping(slave.fqdn):
        return FAILURE, "%s - Slave is offline, cannot get uptime!" % name

    is_unix = True
    failed = False
    output = None
    console = get_console(slave, usebuildbotslave=True)
    try:
        log.debug("running 'uptime'")
        rc, output = console.run_cmd('uptime')
        if rc != 0:
            is_unix = False
            log.debug("running 'net statistics server'")
            rc, output = console.run_cmd('net statistics server')
            if rc != 0:
                failed = True
    except RemoteCommandError:
        failed = True
    if failed:
        return FAILURE, "%s - Neither 'uptime' nor 'net statistics server' commands were successful" % name

    uptime = None
    if is_unix:
        uptime = get_unix_uptime(output)
    else:
        uptime = get_windows_uptime(output)
    if uptime is not None:
        return SUCCESS, uptime
    else:
        return FAILURE, "%s - could not retrieve uptime"
