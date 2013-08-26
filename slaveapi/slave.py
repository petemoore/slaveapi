import time

from bzrest.errors import BugNotFound

from dns import resolver

from . import config
from .clients import inventory, slavealloc
from .clients.bugzilla import ProblemTrackingBug, RebootBug
from .clients.ipmi import IPMIInterface
from .clients.pdu import PDU
from .clients.ping import ping
from .clients.ssh import SSHConsole

import logging
log = logging.getLogger(__name__)


class Slave(object):
    def __init__(self, name):
        if "." not in name:
            name += "." + config["default_domain"]
        answer = resolver.query(name)
        self.name = answer.canonical_name.to_text().split(".")[0]
        self.domain = answer.canonical_name.parent().to_text().rstrip(".")
        self.ip = answer[0].to_text()
        # Per IT, parsing the FQDN is the best way to find the colo.
        # Our hostnames always end in $colo.mozilla.com.
        self.colo = self.fqdn.split(".")[-3]
        self.mgmt = None
        self.bug = None
        self.enabled = None
        self.basedir = None
        self.notes = None
        self.pdu = None

    @property
    def fqdn(self):
        return "%s.%s" % (self.name, self.domain)

    def load_slavealloc_info(self):
        log.info("Getting slavealloc info for %s", self.name)
        debug = slavealloc.get_slave(config["slavealloc_api"], name=self.name)
        self.enabled = debug["enabled"]
        self.basedir = debug["basedir"]
        self.notes = debug["notes"]

    def load_inventory_info(self):
        log.info("Getting inventory info for %s", self.name)
        debug = inventory.get_system(
            self.fqdn, config["inventory_api"], config["inventory_username"],
            config["inventory_password"],
        )
        if debug["pdu_fqdn"]:
            self.pdu = PDU(debug["pdu_fqdn"], debug["pdu_port"])

    def load_ipmi_info(self):
        # Also per IT, the management interface (eg, IPMI), if it exists, can
        # always be found by appending "-mgmt.build.mozilla.org" to the name.
        try:
            mgmt_fqdn = "%s-mgmt.%s" % (self.name, config["default_domain"])
            resolver.query(mgmt_fqdn)
            # This will return None if the IPMI interface doesn't work for some
            # reason.
            self.mgmt = IPMIInterface.get_if_exists(mgmt_fqdn, config["ipmi_username"], config["ipmi_password"])
        except resolver.NXDOMAIN:
            # IPMI Interface doesn't exist.
            pass

    def load_bug_info(self, createIfMissing=False):
        log.info("Getting bug info for %s", self.name)
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.refresh()
        except BugNotFound:
            log.info("Couldn't find bug for %s, creating it...", self.name)
            self.bug.create()

    def ssh_reboot(self):
        console = self._get_console()
        console.reboot()

    def get_reboot_bug(self):
        current_reboot_bug = RebootBug(self.colo)
        # if it's open, attach slave to it
        if current_reboot_bug.data["is_open"]:
            return current_reboot_bug
        else:
            current_reboot_bug.update({"alias": None})
            new_reboot_bug = RebootBug(self.colo, loadInfo=False)
            new_reboot_bug.create()
            return new_reboot_bug

    def is_alive(self, timeout=300):
        log.info("Checking for signs of life on %s", self.name)
        start = time.time()
        while time.time() - start < timeout:
            if ping(self.ip):
                log.debug("Slave is alive")
                return True
            else:
                log.debug("Slave isn't alive yet")
                time.sleep(5)
        else:
            log.error("Timeout of %d exceeded, giving up" % timeout)
            return False
                
    def wait_for_reboot(self, alive_timeout=300, down_timeout=60):
        log.info("Waiting %d seconds for %s to reboot.", down_timeout, self.name)
        # First, wait for the slave to go down.
        start = time.time()
        while time.time() - start < down_timeout:
            if not ping(self.ip, count=1, deadline=2):
                log.debug("Slave is confirmed to be down, waiting for revival.")
                break
            else:
                log.debug("Slave is not down yet...")
                time.sleep(1)
        else:
            log.error("Slave didn't go down in allotted time, assuming it didn't reboot.")
            return False

        # Then wait for it come back up.
        return self.is_alive(timeout=alive_timeout)

    def _get_console(self):
        return SSHConsole(self.fqdn, config["ssh_credentials"])
