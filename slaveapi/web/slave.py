import logging

from flask import Response, make_response, request, jsonify
from flask.views import MethodView

from ..actions.reboot import reboot
from ..global_state import processor, results

log = logging.getLogger(__name__)


class Slave(MethodView):
    def get(self, slave):
        slave = Slave(slave)
        slave.load_all_info()
        return jsonify(res.serialize())


class Reboot(MethodView):
    """Request a reboot of a slave or get status on a previously requested
       reboot."""

    def get(self, slave):
        """Retrieve results from reboots.
        
        URL Args:
            slave (str): The slave to retrieve results for.

        Query Args:
            requestid (int): If specified, returns only the results for this \
                specific reboot request. If not passed, results from all \
                previous reboots are returned.

        Returns:
            The status of the requested specified or the status of all previous
            reboots. See :py:func:`slaveapi.actions.results.ActionResult.serialize`
            for details on what status looks like.
        """
        try:
            requestid = request.args.get("requestid", None)
            if requestid:
                requestid = int(requestid)
                log.debug("%s - Got requestid: %s", slave, requestid)
        except TypeError:
            return Response(response="Couldn't parse requestid", status=400)

        res = results[slave][reboot.__name__].get(requestid, None)
        if res:
            return jsonify(res.serialize())
        else:
            reboots = {}
            for id_, res in results[slave][reboot.__name__].iteritems():
                reboots[id_] = res.serialize()
            return jsonify({"reboots": reboots})

    def post(self, slave):
        """Requests a reboot of a slave.
        
        URL Args:
            slave: The slave to reboot.

        Query Args:
            waittime: How long to wait (in seconds) for a reboot before \
                returning a requestid to the user and continuing the work in \
                the background.

        Returns:
            The status of the reboot, after waiting `waittime` for it to
            complete. See :py:func:`slaveapi.actions.results.ActionResult.serialize`
            for details on what status looks like.
        """
        res = processor.add_work(slave, reboot)
        results[slave][reboot.__name__][res.id_] = res

        # Wait for the action to complete if requested.
        waittime = int(request.form.get("waittime", 0))
        res.wait(waittime)
        data = res.serialize(include_requestid=True)
        if res.is_done():
            return jsonify(data)
        else:
            return make_response(jsonify(data), 202)
