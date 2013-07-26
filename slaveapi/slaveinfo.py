from slaveapi import config

from slavealloc import get_slave

class Slave(object):
    def __init__(self, name):
        self.name = name

    def getSlaveallocInfo(self):
        info = get_slave(name=self.name)
        self.enabled = info['enabled']
        self.basedir = info['basedir']
        self.notes = info['notes']
