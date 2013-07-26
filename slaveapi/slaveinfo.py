from slavealloc import get_slave

import logging
log = logging.getLogger(__name__)

class Slave(object):
    def __init__(self, name):
        self.name = name

    def load_info(self):
        self.load_slavealloc_info()
        self.load_inventory_info()

    def load_slavealloc_info(self):
        log.debug("Getting info for %s", self.name)
        info = get_slave(name=self.name)
        self.enabled = info['enabled']
        self.basedir = info['basedir']
        self.notes = info['notes']

    def load_inventory_info(self):
        pass
