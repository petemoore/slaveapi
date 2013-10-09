from flask import jsonify
from flask.views import MethodView

from ..actions.status import serialize_results
from ..global_state import results


class Results(MethodView):
    """OMG"""
    def get(self):
        """WTF"""
        return jsonify(serialize_results(results))
