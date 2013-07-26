import logging
log = logging.getLogger(__name__)

from slaveapi.slaveinfo import Slave

def reboot(name):
    slave = Slave(name)
    slave.load_slavealloc_info()
