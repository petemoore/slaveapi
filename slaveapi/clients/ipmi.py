from subprocess import check_output, CalledProcessError, STDOUT
import time

import logging
log = logging.getLogger(__name__)

class IPMIInterface(object):
    retry_errors = ["LANPLUS_STATE_PRESESSION", "Unable to establish",
                    "LANPLUS_STATE_OPEN_SESSION_RECEIVED"]
    interface_type = "lanplus"

    def __init__(self, fqdn, username, password):
        self.fqdn = fqdn
        self.username = username
        self.password = password

    @classmethod
    def get_if_exists(cls, fqdn, username, password):
        # If this doesn't raise we can safely assume that "fqdn" has a
        # working IPMI interface.
        interface = cls(fqdn, username, password)
        try:
            interface.run_cmd("mc info")
            return interface
        except CalledProcessError:
            return None

    def poweroff(self, hard=False):
        if hard:
            self.run_cmd("power off")
        else:
            self.run_cmd("power soft")

    def poweron(self):
        self.run_cmd("power on")

    def powercycle(self, delay=5):
        log.info("Powercycling")
        log.debug("Trying soft shutdown.")
        self.poweroff(hard=False)
        if self.wait_for_off():
            log.debug("Soft shutdown succeeded.")
        else:
            log.debug("Soft shutdown failed, trying a hard shutdown.")
            self.poweroff(hard=True)
            if self.wait_for_off():
                log.debug("Hard shutdown succeeded.")
            else:
                raise Exception()
        log.debug("Waiting %d seconds before powering on.", delay)
        time.sleep(delay)
        log.debug("Turning machine back on.")
        self.poweron()
        log.info("Powercycle completed.")

    def wait_for_off(self, wait=120):
        time_left = 120
        while True:
            if "off" in self.run_cmd("power status"):
                return True
            else:
                if time_left <= 0:
                    return False
                time_left -= 15
                time.sleep(15)

    def run_cmd(self, cmd, retries=5):
        full_cmd = ["ipmitool", "-H", self.fqdn, "-I", self.interface_type,
                    "-U", self.username, "-P", self.password]
        full_cmd += cmd.split()
        attempt = 1
        while attempt <= retries:
            try:
                return check_output(full_cmd, stderr=STDOUT)
            except CalledProcessError, e:
                # IPMI tends to be a bit flakey. ipmitool often returns -6
                # when it can't establish a session, but there's also some
                # other cases that don't return a distinct enough error code
                # to retry with. We need to handle those cases separately.
                for error in self.retry_errors:
                    if error in e.output:
                        attempt += 1
                        break
                if e.returncode == -6:
                    attempt += 1
                    continue
                log.info("Unable to establish IPMI session, retrying...")
                log.debug("Return code was %d, output was:", e.returncode)
                log.debug(e.output)
                raise
