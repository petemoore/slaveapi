import time

from bzrest.errors import BugNotFound

from dns import resolver

from furl import furl

from .clients import inventory, slavealloc
from .clients.bugzilla import ProblemTrackingBug, RebootBug
from .clients.buildapi import get_recent_jobs
from .clients.ipmi import IPMIInterface
from .clients.pdu import PDU
from .clients.ping import ping
from .clients.ssh import SSHConsole
from .global_state import config

import logging
log = logging.getLogger(__name__)

def windows2msys(path_):
    (drive, therest) = path_.split(":")
    return "/" + drive[0] + therest.replace("\\", "/")

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
        self.ipmi = None
        self.bug = None
        self.enabled = None
        self.basedir = None
        self.notes = None
        self.pdu = None

    @property
    def fqdn(self):
        return "%s.%s" % (self.name, self.domain)

    def load_all_info(self):
        self.load_slavealloc_info()
        self.load_inventory_info()
        self.load_ipmi_info()
        self.load_bug_info()
        self.load_recent_job_info()

    def load_slavealloc_info(self):
        log.info("%s - Getting slavealloc info", self.name)
        info = slavealloc.get_slave(config["slavealloc_api_url"], name=self.name)
        master_info = slavealloc.get_master(config["slavealloc_api_url"], info["current_masterid"])
        self.enabled = info["enabled"]
        self.basedir = info["basedir"].rstrip("/")
        # Because we always work with UNIX style paths in SlaveAPI we need
        # to massage basedir when a Windows style one is detected.
        if self.basedir[1] == ":":
            self.basedir = windows2msys(self.basedir)
        self.notes = info["notes"]
        self.master = master_info["fqdn"]
        self.master_url = furl().set(scheme="http", host=self.master, port=master_info["http_port"])

    def load_inventory_info(self):
        log.info("%s - Getting inventory info", self.name)
        info = inventory.get_system(
            self.fqdn, config["inventory_api_url"], config["inventory_username"],
            config["inventory_password"],
        )
        if info["pdu_fqdn"]:
            self.pdu = PDU(info["pdu_fqdn"], info["pdu_port"])

    def load_ipmi_info(self):
        # Also per IT, the IPMI Interface, if it exists, can
        # always be found by appending "-mgmt.build.mozilla.org" to the name.
        try:
            ipmi_fqdn = "%s-mgmt.%s" % (self.name, config["default_domain"])
            resolver.query(ipmi_fqdn)
            # This will return None if the IPMI interface doesn't work for some
            # reason.
            self.ipmi = IPMIInterface.get_if_exists(ipmi_fqdn, config["ipmi_username"], config["ipmi_password"])
        except resolver.NXDOMAIN:
            # IPMI Interface doesn't exist.
            pass

    def load_bug_info(self, createIfMissing=False):
        log.info("%s - Getting bug info", self.name)
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.refresh()
        except BugNotFound:
            if createIfMissing:
                log.info("%s - Couldn't find bug, creating it...", self.name)
                self.bug.create()
                self.bug.refresh()

    def load_recent_job_info(self, n_jobs=1):
        log.info("%s - Getting recent job info", self.name)
        self.recent_jobs = get_recent_jobs(
            self.name, config["buildapi_api_url"], n_jobs=n_jobs
        )

    def to_dict(self):
        """Serializes the state of a Slave. It is up to the caller to ensure that
        any desired information (slavealloc, etc.) is loaded prior to
        serialization."""

        data = {
            "fqdn": self.fqdn,
            "domain": self.domain,
            "ip": self.ip,
            "colo": self.colo,
            "enabled": self.enabled,
            "basedir": self.basedir,
            "notes": self.notes,
            "bug": None,
            "ipmi": None,
            "pdu": None,
            "recent_jobs": self.recent_jobs
        }
        if self.bug.data:
            data["bug"] = {
                "id": self.bug.id_,
                "is_open": self.bug.data["is_open"]
            }
        if self.ipmi:
            data["ipmi"] = {
                "fqdn": self.ipmi.fqdn,
            }
        if self.pdu:
            data["pdu"] = {
                "fqdn": self.pdu.fqdn,
                "port": self.pdu.port,
            }
        return data


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
