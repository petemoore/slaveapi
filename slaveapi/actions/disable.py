import logging

from ..clients import slavealloc
from ..slave import Slave
from .reboot import reboot
from .shutdown_buildslave import shutdown_buildslave
from .results import SUCCESS
from ..global_state import config

log = logging.getLogger(__name__)

def disable(name, reason=None, force=False):
    """Attempts to disable the named slave from buildbot.

    Details of what was attempted and the result are reported into the
    slave's problem tracking bug at the end.

    Disabling is done in a series of steps outlined below:

    1. Disable In Slavealloc: unchecks enabled box for slave in slavealloc

    2. Stop Buildbot Process: stops buildbot process by either a calling a
        graceful_shutdown or a more aggressive forceful reboot.

    3. Update Problem Tracking Bug: reopen problem tracking bug and leave
        comment if a 'comment' field was passed

    :param name: hostname of slave
    :type name: str
    :param reason: reason we wish to disable the slave
    :type reason: str
    :param force: force a reboot immediately instead of graceful_shutdown
    :type force: bool

    :rtype: tuple
    """
    status_msgs = ["Disabling Slave: %s by..." % name]
    return_code = SUCCESS  # innocent until proven guilty!

    slave = Slave(name)
    slave.load_slavealloc_info()
    slave.load_bug_info(createIfMissing=True)

    if not slave.enabled:  # slave disabled in slavealloc, nothing to do!
        status_msgs.append("Slave is already disabled. Nothing to do.")
        return return_code, "\n".join(status_msgs)

    #### 1. Disable Slave in Slavealloc
    slavealloc_values = {
        'enabled': False,
    }
    return_code, update_alloc_msg = slavealloc.update_slave(
        api=config["slavealloc_api_url"], name=name,
        data=slavealloc_values,
    )
    status_msgs.append(str(update_alloc_msg))
    ####

    #### 2. Stop Buildbot Process
    if return_code == SUCCESS:
        if force:
            status_msgs.append("Forcing a reboot.")
            # don't let reboot() update bug; we'll do it at end of this action
            return_code, reboot_msg = reboot(name, update_bug=False)
            status_msgs.append(str(reboot_msg))
        else:
            return_code, stop_buildslave_msg = shutdown_buildslave(name)
            status_msgs.append(str(stop_buildslave_msg))
    ####

    #### 3. Update Problem Tracking Bug
    if return_code == SUCCESS:
        status_msgs.append("%s - was successfully disabled via slaveapi" % name)
        if reason:
            status_msgs.append("Reason for disabling: %s" % reason)
    else:
        status_msgs.append("%s - Couldn't be confirmed disabled via slaveapi" % name)

    bug_data = {}
    if not slave.bug.data["is_open"]:
        bug_data["status"] = "REOPENED"
    slave.bug.add_comment("\n".join(status_msgs), data=bug_data)
    ###

    return return_code, "\n".join(status_msgs)
