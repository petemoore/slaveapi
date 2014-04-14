import logging

from flask import jsonify
from flask.views import MethodView

from .action_base import ActionView
from ..actions.reboot import reboot
from ..actions.shutdown_buildslave import shutdown_buildslave
from ..actions.buildslave_uptime import buildslave_uptime
from ..actions.buildslave_last_activity import buildslave_last_activity
from ..slave import Slave as SlaveClass

log = logging.getLogger(__name__)


class Slave(MethodView):
    def get(self, slave):
        slave = SlaveClass(slave)
        slave.load_all_info()
        return jsonify(slave.to_dict())


class Reboot(ActionView):
    """Request a reboot of a slave or get status on a previously requested
    reboot. See :py:class:`slaveapi.web.action_base.ActionView` for details
    on GET and POST methods. See :py:func:`slaveapi.actions.reboot.reboot` for
    details on how reboots are performed."""

    def __init__(self, *args, **kwargs):
        self.action = reboot
        ActionView.__init__(self, *args, **kwargs)


class ShutdownBuildslave(ActionView):
    """Request a shutdown of a buildslave or get status on a previously requested
    shutdown. See :py:class:`slaveapi.web.action_base.ActionView` for details
    on GET and POST methods. See :py:func:`slaveapi.actions.shutdown_buildslave.shutdown_buildslave`
    for details on how buildslave shutdowns are performed."""
    def __init__(self, *args, **kwargs):
        self.action = shutdown_buildslave
        ActionView.__init__(self, *args, **kwargs)

class GetUptime(ActionView):
    """Request the build slave uptime (in seconds).  See
    :py:class:`slaveapi.web.action_base.ActionView` for details on GET and POST
    methods. See :py:func:`slaveapi.actions.buildslave_uptime.buildslave_uptime`
    for details on how Uptime is retrieved."""
    def __init__(self, *args, **kwargs):
        self.action = buildslave_uptime
        ActionView.__init__(self, *args, **kwargs)

class GetLastActivity(ActionView):
    """Request the last activity age (in seconds).  See
    :py:class:`slaveapi.web.action_base.ActionView` for details on GET and POST
    methods. See :py:func:`slaveapi.actions.buildslave_last_activity.buildslave_last_activity`
    for details on how LastActivity is retrieved."""
    def __init__(self, *args, **kwargs):
        self.action = buildslave_last_activity
        ActionView.__init__(self, *args, **kwargs)
