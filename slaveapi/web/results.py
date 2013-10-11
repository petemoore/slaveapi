from flask import jsonify
from flask.views import MethodView

from ..actions.results import serialize_results
from ..global_state import results


class Results(MethodView):
    """Provides results from previously requested actions."""
    def get(self):
        """Returns all results from all previously requested actions in JSON
        format.

        Returns:
            See :py:func:`slaveapi.actions.results.serialize_results` for
            details on the format of the returned data.
        """
        return jsonify(serialize_results(results))
