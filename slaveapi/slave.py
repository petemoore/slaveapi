from bzrest.errors import BugzillaAPIError, INVALID_ALIAS, INVALID_BUG

from dns import resolver

from paramiko import SSHClient

from . import config, inventory, slavealloc
from .bugzilla import ProblemTrackingBug

import logging
log = logging.getLogger(__name__)


class PDU(object):
    def __init__(self, fqdn, port):
        self.fqdn = fqdn
        self.port = port

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, delay=None):
        pass

class MgmtInterface(object):
    def __init__(self, fqdn):
        self.fqdn = fqdn

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, hard=False):
        pass


class IgnorePolicy(object):
    def missing_host_key(self, *args):
        pass

class RemoteConsole(object):
    def __init__(self, connect=True):
        self.conn = SSHClient()
        self.conn.set_missing_host_key_policy(IgnorePolicy())
        if connect:
            self.connect()

    def connect(self, credentials):
        pass


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
        # Also per IT, the management interface (eg, IPMI), if it exists, can
        # always be found by appending "-mgmt.build.mozilla.org" to the name.
        try:
            mgmt_fqdn = "%s-mgmt.%s" % (self.name, config["default_domain"])
            resolver.query(mgmt_fqdn)
            self.mgmt = MgmtInterface(mgmt_fqdn)
        except resolver.NXDOMAIN:
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
        log.debug("Getting slavealloc info for %s", self.name)
        info = slavealloc.get_slave(config["slavealloc_api"], name=self.name)
        self.enabled = info["enabled"]
        self.basedir = info["basedir"]
        self.notes = info["notes"]

    def load_inventory_info(self):
        log.debug("Getting inventory info for %s", self.name)
        info = inventory.get_system(
            self.fqdn, config["inventory_api"], config["inventory_username"],
            config["inventory_password"],
        )
        if info["pdu_fqdn"]:
            self.pdu = PDU(info["pdu_fqdn"], info["pdu_port"])

    def load_bug_info(self, create=False):
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.load_bug_info()
        except BugzillaAPIError as e:
            if e.bugzilla_code in (INVALID_ALIAS, INVALID_BUG) and create:
                self.bug.create(config["bugzilla_product"], config["bugzilla_component"])
            else:
                raise

    def ssh_reboot(self):
        conn = SSHClient()

    def is_alive(self, timeout=300):
        pass
