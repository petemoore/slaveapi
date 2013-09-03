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
                log.debug("%s - Got requestid: %s", slave, requestid)
        except TypeError:
            return Response(response="Couldn't parse requestid", status=400)

        res = results[slave][reboot.__name__].get(requestid, None)
        if res:
            return res.json()
        else:
            reboots = {}
            for id_, res in results[slave][reboot.__name__].iteritems():
                reboots[id_] = res.json()
            return jsonify({"reboots": reboots})

    def post(self, slave):
        res = processor.add_work(slave, reboot)
        results[slave][reboot.__name__][res.id_] = res

        # Wait for the action to complete if requested.
        waittime = int(request.form.get("waittime", 0))
        res.wait(waittime)
        data = res.json(include_requestid=True)
        if res.is_done():
            return jsonify(data)
        else:
            return make_response(jsonify(data), 202)
