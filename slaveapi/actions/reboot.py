import time

from ..slave import Slave

import logging
log = logging.getLogger(__name__)

def reboot(name):
    bug_comment = ""
    slave = Slave(name)
    slave.load_inventory_info()
    slave.load_bug_info(createIfMissing=True)
    bug_comment += "Attempting SSH reboot..."

    alive = False
    # Try an SSH reboot first of all...
    try:
        slave.ssh_reboot()
        # Wait a few seconds before checking for aliveness, because the slave may
        # still accept connections directly after asking for the reboot.
        time.sleep(3)
        alive = slave.is_alive()
    except:
        log.exception("Caught exception.")

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
        # We've done all we can - now we need human involvement to get the
        # machine back online.
        reboot_bug = slave.get_reboot_bug()
        bug_comment += "Failed.\n"
        bug_comment += "Can't do anything else, human intervention needed."
        data = {
            "depends_on": {
                "add": [reboot_bug.id_],
            }
        }
        slave.bug.add_comment(bug_comment, data)
