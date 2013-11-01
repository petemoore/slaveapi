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
    action = reboot


class ShutdownBuildslave(MethodView):
    action = shutdown_buildslave
