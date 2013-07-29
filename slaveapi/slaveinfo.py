from slavealloc import get_slave

import logging
log = logging.getLogger(__name__)


class PDU(object):
    def __init__(self):
        self.ip = None

    def off(self):
    def on(self):
    def powercycle(self, delay=None):

class OOBInterface(object):
    def __init__(self):
        self.ip = None

    def off(self):
    def on(self):
    def powercycle(self, hard=False):

class Slave(object):
    def __init__(self, name):
        self.name = name
        self.bug = None

    # TODO: should cache this stuff
    def load_info(self):
        self.load_slavealloc_info()
        self.load_inventory_info()

    def load_slavealloc_info(self):
        log.debug("Getting slavealloc info for %s", self.name)
        info = get_slave(name=self.name)
        self.enabled = info['enabled']
        self.basedir = info['basedir']
        self.notes = info['notes']

    def load_inventory_info(self):
        log.debug("Getting inventory info for %s", self.name)
        self.pdu = None
        self.ip = None
        self.fqdn = None
        self.oob = None

    def load_bug_info(self, create=False):
        self.bug = ProblemTrackingBug(self.name)
