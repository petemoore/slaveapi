import time

from dns import resolver

from ..clients import inventory
from ..clients.ipmi import IPMIInterface
from ..clients.pdu import PDU
from ..clients.ping import ping
from ..global_state import config

import logging
log = logging.getLogger(__name__)

class Machine(object):
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
        self.pdu = None

    @property
    def fqdn(self):
        return "%s.%s" % (self.name, self.domain)

    def load_all_info(self):
        self.load_inventory_info()
        self.load_ipmi_info()

    def load_inventory_info(self):
        """ Loads useful data from inventory.

        Sets the self.pdu object
        Uses self.fqdn"""

        log.info("Getting inventory info")
        info = inventory.get_system(
            self.fqdn, config["inventory_api_url"], config["inventory_username"],
            config["inventory_password"],
        )
        if info["pdu_fqdn"]:
            self.pdu = PDU(info["pdu_fqdn"], info["pdu_port"])
        # Return info to allow subclasses to do stuff with data, without refetching
        return info

    def load_ipmi_info(self):
        """ Loads ipmi info for this machine if it exists.
        By querying DNS for a -mgmt hostname, and checks it.

        Sets the self.ipmi object"""

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

    def to_dict(self):
        """Serializes the state of a Machine. It is up to the caller to ensure that
        any desired information (slavealloc, etc.) is loaded prior to
        serialization."""

        data = {
            "fqdn": self.fqdn,
            "domain": self.domain,
            "ip": self.ip,
            "colo": self.colo,
            "ipmi": None,
            "pdu": None,
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

def is_alive(machine, timeout=300):
    log.info("Checking for signs of life")
    start = time.time()
    while time.time() - start < timeout:
        if ping(machine.ip):
            log.debug("Machine is alive")
            return True
        else:
            log.debug("Machine isn't alive yet")
            time.sleep(5)
    else:
        log.error("Timeout of %d exceeded, giving up", timeout)
        return False

def wait_for_reboot(machine, alive_timeout=300, down_timeout=60):
    log.info("Waiting %d seconds for reboot.", down_timeout)
    # First, wait for the machine to go down.
    start = time.time()
    while time.time() - start < down_timeout:
        if not ping(machine.ip, count=1, deadline=2):
            log.debug("Machine is confirmed to be down, waiting for revival.")
            break
        else:
            log.debug("Machine is not down yet...")
            time.sleep(1)
    else:
        log.error("Machine didn't go down in allotted time, assuming it didn't reboot.")
        return False

    # Then wait for it come back up.
    return is_alive(machine, timeout=alive_timeout)
