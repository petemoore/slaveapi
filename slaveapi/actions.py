import logging
log = logging.getLogger(__name__)

from .slave import Slave

def reboot(name):
    bug_comment = ""
    slave = Slave(name)
    slave.load_inventory_info()
    slave.load_bug_info(createIfMissing=True)
    bug_comment += "Attempting SSH reboot..."

    # Try an SSH reboot first of all...
    slave.ssh_reboot()
    alive = slave.is_alive()

    # If that doesn't work, maybe an mgmt reboot will...
    if not alive and slave.mgmt:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting management interface reboot..."
        slave.mgmt.powercycle()
        alive = slave.is_alive()

    # Is mgmt interface _and_ PDU a valid configuration?
    # Mayhaps a PDU reboot?
    if not alive and slave.pdu:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting PDU reboot..."
        slave.pdu.powercycle()
        alive = slave.is_alive()

    if alive:
        bug_comment += "Success!"
        slave.bug.add_comment(bug_comment)
    else:
        # TODO: Get IT involved - reboot bug
        bug_comment += "Failed.\n"
        bug_comment += "Can't do anything else, human intervention needed."
        slave.bug.reopen(bug_comment)
