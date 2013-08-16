import logging

from flask import Response
from flask.views import MethodView

from .. import pending, processor
from ..actions import reboot

log = logging.getLogger(__name__)


class Reboot(MethodView):
    def get(self, slave):
        id_  = (slave, reboot.__name__)
        if id_ in pending:
            return Response(status=202)
        else:
            # return status of last reboot?
            return Response(status=200)

    def post(self, slave):
        id_ = (slave, "reboot")
        if id_ not in pending:
            e = processor.add_work(slave, reboot)
            pending[id_] = e
        else:
            e = pending[id_]
        return Response(status=202)
