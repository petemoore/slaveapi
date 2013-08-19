import logging

from flask import Response, make_response, jsonify, request
from flask.views import MethodView

from .. import pending, processor
from ..actions import reboot

log = logging.getLogger(__name__)


class Reboot(MethodView):
    def get(self, slave):
        requestid = request.query_string.get("requestid")
        if requestid and requestid in pending[slave]["reboot"]:
            return Response(response="Request %d is pending" % requestid, status=202)
        elif len(pending[slave]["reboot"]) > 0:
            msg = "Pending reboots: %s" % pending[slave]["reboot"]
            return Response(response=msg, status=202)
        else:
            return Response(response="No reboots pending", status=200)

    def post(self, slave):
        e = processor.add_work(slave, reboot)
        requestid = id(e)
        pending[slave]["reboot"].append(requestid)
        return make_response(jsonify({"requestid": requestid}), status=202)
