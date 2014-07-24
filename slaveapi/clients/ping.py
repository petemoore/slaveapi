import logging
from subprocess import check_output, STDOUT, CalledProcessError

log = logging.getLogger(__name__)

def ping(host, count=4, deadline=None):
    """Tries to ping "host". Returns True if all request packets recieve a
       a reply and False otherwise."""
    cmd = ["ping", "-c", str(count)]
    if deadline:
        cmd += ["-w", str(deadline), "-W", str(deadline)]
    cmd += [host]
    try:
        output = check_output(cmd, stderr=STDOUT)
    except CalledProcessError, e:
        output = e.output
    if " 0% packet loss" in output:
        log.debug("ping was successful")
        return True
    log.debug("ping failed")
    return False
