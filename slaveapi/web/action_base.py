import logging

from flask import jsonify, make_response, request, Response
from flask.views import MethodView

from ..global_state import processor, results

log = logging.getLogger(__name__)


class ActionView(MethodView):
    action = NotImplementedError

    def get(self, slave):
        try:
            requestid = request.args.get("requestid", None)
            if requestid:
                requestid = int(requestid)
                log.debug("%s - Got requestid: %s", slave, requestid)
        except TypeError:
            return Response(response="Couldn't parse requestid", status=400)

        res = results[slave][self.action.__name__].get(requestid, None)
        if res:
            return jsonify(res.to_dict())
        else:
            action_results = {}
            for id_, res in results[slave][self.action.__name__].iteritems():
                action_results[id_] = res.to_dict()
            return jsonify({self.action.__name__: action_results})

    def post(self, slave):
        res = processor.add_work(slave, self.action)
        results[slave][self.action.__name__][res.id_] = res

        # Wait for the action to complete if requested.
        waittime = int(request.form.get("waittime", 0))
        res.wait(waittime)
        data = res.to_dict(include_requestid=True)
        if res.is_done():
            return jsonify(data)
        else:
            return make_response(jsonify(data), 202)
