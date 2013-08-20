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
        results[slave][reboot.__name__][res.id_] = res

        # Wait for the action to complete if requested.
        waittime = int(request.form.get("waittime", 0))
        res.wait(waittime)
        data = {"state": res.state, "msg": res.msg, "requestid": res.id_}
        if res.is_done():
            return jsonify(data)
        else:
            return make_response(jsonify(data), 202)
