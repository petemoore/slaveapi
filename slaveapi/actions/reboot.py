from .results import SUCCESS, FAILURE
from ..slave import Slave, get_reboot_bug, wait_for_reboot, get_console

import logging
log = logging.getLogger(__name__)

def reboot(name):
    """Attempts to reboot the named slave a series of ways, escalating from
    peacefully to mercilessly. Details of what was attempted and the result
    are reported into the slave's problem tracking bug at the end. Reboots
    are attempted through the following means (from most peaceful to least
    merciful):

    * SSH: Logs into the machine via SSH and reboots it with an \
        appropriate command.

    * IPMI: Uses the slave's IPMI interface to initiate a hard \
        reboot. If the slave has no IPMI interface, this is skipped.

    * PDU: Powercycles the slave by turning off the power, and then \
        turning it back on.

    * Bugzilla: Requests that IT reboot the slave by updating or creating \
        the appropriate bugs.
    """
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
        log.exception("%s - Caught exception.", name)

    # If that doesn't work, maybe an IPMI reboot will...
    if not alive and slave.ipmi:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting IPMI reboot..."
        slave.ipmi.powercycle()
        alive = wait_for_reboot(slave)

    # Mayhaps a PDU reboot?
    if not alive and slave.pdu:
        bug_comment += "Failed.\n"
        bug_comment += "Attempting PDU reboot..."
        slave.pdu.powercycle()
        alive = wait_for_reboot(slave)

    if alive:
        bug_comment += "Success!"
        slave.bug.add_comment(bug_comment)
        return SUCCESS, bug_comment
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
        return FAILURE, bug_comment
