from slavealloc import get_slave

import logging
log = logging.getLogger(__name__)

class Slave(object):
    def __init__(self, name):
        self.name = name

    def load_slavealloc_info(self):
        log.debug("Getting info for %s", self.name)
        info = get_slave(name=self.name)
        print info
        self.enabled = info['enabled']
        self.basedir = info['basedir']
        self.notes = info['notes']
        log.debug("Got info: %s", self.notes)
