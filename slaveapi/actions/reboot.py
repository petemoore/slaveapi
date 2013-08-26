from ..slave import Slave, get_reboot_bug, wait_for_reboot, get_console

import logging
log = logging.getLogger(__name__)

def reboot(name):
    bug_comment = ""
    slave = Slave(name)
    slave.load_inventory_info()
    slave.load_ipmi_info()
    slave.load_bug_info(createIfMissing=True)
    bug_comment += "Attempting SSH reboot..."

    alive = False
    # Try an SSH reboot first of all...
    try:
        console = get_console(slave)
        console.reboot()
        alive = wait_for_reboot(slave)
    except:
        log.exception("Caught exception.")

    # If that doesn't work, maybe an mgmt reboot will...
    if not alive and slave.mgmt:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting management interface reboot..."
        slave.mgmt.powercycle()
        alive = wait_for_reboot(slave)

    # Is mgmt interface _and_ PDU a valid configuration?
    # Mayhaps a PDU reboot?
    if not alive and slave.pdu:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting PDU reboot..."
        slave.pdu.powercycle()
        alive = wait_for_reboot(slave)

    if alive:
        bug_comment += "Success!"
        slave.bug.add_comment(bug_comment)
    else:
        # We've done all we can - now we need human involvement to get the
        # machine back online.
        reboot_bug = get_reboot_bug(slave)
        bug_comment += "Failed.\n"
        bug_comment += "Can't do anything else, human intervention needed."
        data = {
            "depends_on": {
                "add": [reboot_bug.id_],
            }
        }
        slave.bug.add_comment(bug_comment, data)
