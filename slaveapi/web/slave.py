import logging

from flask import Response, make_response, json, request, jsonify
from flask.views import MethodView

from .. import processor, status
from ..actions import reboot

log = logging.getLogger(__name__)


class Reboot(MethodView):
    def get(self, slave):
        try:
            requestid = request.args.get("requestid", None)
            if requestid:
                requestid = int(requestid)
                log.debug("Got requestid: %s" % requestid)
        except TypeError:
            return Response(response="Couldn't parse requestid", status=400)

        s = status[slave][reboot.__name__].get(requestid, None)
        if s:
            return jsonify({"state": s.state, "result": s.result})
        elif len(status[slave][reboot.__name__]) > 0:
            return jsonify({"reboots": status[slave][reboot.__name__]})
        else:
            return Response(response="No reboots found", status=200)

    def post(self, slave):
        s = processor.add_work(slave, reboot)
        requestid = id(s)
        status[slave][reboot.__name__].append(requestid)
        return make_response(json.dumps({"requestid": requestid}), 202)
