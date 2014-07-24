import logging

from flask import jsonify, make_response, request, Response
from flask.views import MethodView

from ..global_state import processor, results

log = logging.getLogger(__name__)


class ActionView(MethodView):
    """Abstract base class for views that expose actions. Subclasses must
    set "action", which should be a callable that accepts a slave name as
    its first argument. Subclasses should set this in their __init__ rather
    than as a class attribute, otherwise Python will turn it into a class
    method and pass along "self" to the action -- which actions don't generally
    expect. If the action requires extra arguments (eg, arguments
    sent through POST data), the subclass should override the "post" method
    and pass them to it."""
    action = NotImplementedError

    def get(self, slave):
        """Retrieve results from an action.

        URL Args:
            slave (str): The slave to retrieve results for.

        Query Args:
            requestid (int): If specified, returns only the results for this \
                specific previous action.. If not passed, results from all \
                previous actions of this type are returned.

        Returns:
            The status of the request specified or the status of all previous
            actions of this type. See :py:func:`slaveapi.actions.results.ActionResult.to_dict`
            for details on what status looks like.
        """
        try:
            requestid = request.args.get("requestid", None)
            if requestid:
                requestid = int(requestid)
                log.debug("Got requestid: %s", requestid)
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

    def post(self, slave, *action_args, **action_kwargs):
        """Request an action of a slave.

        URL Args:
            slave: The slave to perform the action against.

        Query Args:
            waittime: How long to wait (in seconds) for the action to complete before \
                returning a requestid to the user and continuing the work in \
                the background.

        Returns:
            The status of the action, after waiting `waittime` for it to
            complete. See :py:func:`slaveapi.actions.results.ActionResult.to_dict`
            for details on what status looks like.
        """
        res = processor.add_work(slave, self.action, *action_args, **action_kwargs)
        results[slave][self.action.__name__][res.id_] = res

        # Wait for the action to complete if requested.
        waittime = int(request.form.get("waittime", 0))
        res.wait(waittime)
        data = res.to_dict(include_requestid=True)
        if res.is_done():
            return jsonify(data)
        else:
            return make_response(jsonify(data), 202)
