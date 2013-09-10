import time

from bzrest.errors import BugNotFound

from DNS import dnslookup
import DNS.Base

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
        # dnslookup returns both CNAME resolution and IP addresses.
        answer = dnslookup(name, 'A')[-1]
        # The last entry in the return value is always the IP address.
        self.ip = answer[-1]
        # If there's additional entries in the list, they're the CNAME
        # resolution. They appear before the IP address in the return value,
        # the last of which is the fully resolved CNAME.
        if len(answer) > 1:
            canonical_name = answer[-2]
        else:
            canonical_name = name
        self.name, self.domain = canonical_name.split(".", 1)
        self.ip = answer[0].to_text()
        # Per IT, parsing the FQDN is the best way to find the colo.
        # Our hostnames always end in $colo.mozilla.com.
        self.colo = self.fqdn.split(".")[-3]
        self.ipmi = None
        self.bug = None
        self.enabled = None
        self.basedir = None
        self.notes = None
        self.pdu = None

    @property
    def fqdn(self):
        return "%s.%s" % (self.name, self.domain)

    def load_slavealloc_info(self):
        log.info("%s - Getting slavealloc info", self.name)
        debug = slavealloc.get_slave(config["slavealloc_api"], name=self.name)
        self.enabled = debug["enabled"]
        self.basedir = debug["basedir"]
        self.notes = debug["notes"]

    def load_inventory_info(self):
        log.info("%s - Getting inventory info", self.name)
        debug = inventory.get_system(
            self.fqdn, config["inventory_api"], config["inventory_username"],
            config["inventory_password"],
        )
        if debug["pdu_fqdn"]:
            self.pdu = PDU(debug["pdu_fqdn"], debug["pdu_port"])

    def load_ipmi_info(self):
        # Also per IT, the IPMI Interface, if it exists, can
        # always be found by appending "-mgmt.build.mozilla.org" to the name.
        try:
            ipmi_fqdn = "%s-mgmt.%s" % (self.name, config["default_domain"])
            dnslookup(ipmi_fqdn, 'A')
            # This will return None if the IPMI interface doesn't work for some
            # reason.
            self.ipmi = IPMIInterface.get_if_exists(ipmi_fqdn, config["ipmi_username"], config["ipmi_password"])
        except DNS.Base.ServerError:
            # IPMI Interface doesn't exist.
            pass

    def load_bug_info(self, createIfMissing=False):
        log.info("%s - Getting bug info", self.name)
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.refresh()
        except BugNotFound:
            log.info("%s - Couldn't find bug, creating it...", self.name)
            self.bug.create()


def get_reboot_bug(slave):
    try:
        current_reboot_bug = RebootBug(slave.colo, loadInfo=False)
        current_reboot_bug.refresh()
        # if it's open, attach slave to it
        if current_reboot_bug.data["is_open"]:
            return current_reboot_bug
        else:
            current_reboot_bug.update({"alias": None})
            # New reboot bug will be created below.
    except BugNotFound:
        # Will be created below.
        pass
    log.info("%s - Creating new reboot bug for %s", slave.name, slave.colo)
    new_reboot_bug = RebootBug(slave.colo, loadInfo=False)
    new_reboot_bug.create()
    return new_reboot_bug

def is_alive(slave, timeout=300):
    log.info("%s - Checking for signs of life", slave.name)
    start = time.time()
    while time.time() - start < timeout:
        if ping(slave.ip):
            log.debug("%s - Slave is alive", slave.name)
            return True
        else:
            log.debug("%s - Slave isn't alive yet", slave.name)
            time.sleep(5)
    else:
        log.error("%s - Timeout of %d exceeded, giving up", slave.name, timeout)
        return False

def wait_for_reboot(slave, alive_timeout=300, down_timeout=60):
    log.info("%s - Waiting %d seconds for reboot.", slave.name, down_timeout)
    # First, wait for the slave to go down.
    start = time.time()
    while time.time() - start < down_timeout:
        if not ping(slave.ip, count=1, deadline=2):
            log.debug("%s - Slave is confirmed to be down, waiting for revival.", slave.name)
            break
        else:
            log.debug("%s - Slave is not down yet...", slave.name)
            time.sleep(1)
    else:
        log.error("%s - Slave didn't go down in allotted time, assuming it didn't reboot.", slave.name)
        return False

    # Then wait for it come back up.
    return is_alive(slave, timeout=alive_timeout)

def get_console(slave):
    return SSHConsole(slave.ip, config["ssh_credentials"])
