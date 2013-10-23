from flask import jsonify, request
from flask.views import MethodView

from ..clients.slavealloc import get_slaves
from ..global_state import config

class Slaves(MethodView):
    """Provides a filterable list of slaves."""
    def get(self):
        """Returns a list of slaves, sourced from Slavealloc. If multiple
        query args are passed only slaves that meet all of the conditions
        will be returned.

        Query args:
            purpose: Same as Slavealloc's "purpose".
            environ: Same as Slavealloc's "environ".
            pool: Same as Slavealloc's "pool".

        Returns:
            A JSON-encoded list of the requested types of slaves.
        """
        purpose = request.args.getlist("purpose")
        environment = request.args.getlist("environment")
        pool = request.args.getlist("pool")
        enabled = request.args.get("enabled", None)
        slaves = get_slaves(config["slavealloc_api_url"], purpose, environment, pool, enabled)
        return jsonify({"slaves": slaves})
