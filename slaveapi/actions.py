import logging
log = logging.getLogger(__name__)

from .slaveinfo import Slave

def reboot(name):
    slave = Slave(name)
    slave.load_inventory_info()
    slave.load_bug_info()
    print slave.name
    print slave.domain
    print slave.ip
    print slave.colo
    if slave.mgmt:
        print slave.mgmt.fqdn
    if slave.pdu:
        print slave.pdu.fqdn
        print slave.pdu.port
    # update bugzilla during all of these
    # can we update bugzilla with a log handler?
    # try to do an ssh reboot
    # try to do an oob reboot
    # try to do a pdu reboot
    # file IT bug

    # is there anything with oob AND pdu?
