import logging

from flask import jsonify
from flask.views import MethodView

from .action_base import ActionView
from ..actions.reboot import reboot
from ..actions.shutdown_buildslave import shutdown_buildslave
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
    action = reboot


class ShutdownBuildslave(MethodView):
    """Request a shutdown of a buildslave or get status on a previously requested
    shutdown. See :py:class:`slaveapi.web.action_base.ActionView` for details
    on GET and POST methods. See :py:func:`slaveapi.actions.shutdown_buildslave.shutdown_buildslave`
    for details on how buildslave shutdowns are performed."""
    action = shutdown_buildslave
