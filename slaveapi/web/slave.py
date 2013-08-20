import logging

from flask import Response, make_response, request, jsonify
from flask.views import MethodView

from .. import processor, results
from ..actions.reboot import reboot

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

        res = results[slave][reboot.__name__].get(requestid, None)
        if res:
            return jsonify({"state": res.state, "msg": res.msg})
        else:
            reboots = {}
            for id_, res in results[slave][reboot.__name__].iteritems():
                reboots[id_] = {"state": res.state, "msg": res.msg}
            return jsonify({"reboots": reboots})

    def post(self, slave):
        res = processor.add_work(slave, reboot)
        requestid = id(res)
        results[slave][reboot.__name__][requestid] = res
        return make_response(jsonify({"requestid": requestid}), 202)
