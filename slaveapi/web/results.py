from flask import jsonify
from flask.views import MethodView

from ..actions.status import serialize_results
from ..global_state import results


class Results(MethodView):
    def get(self):
        return jsonify(serialize_results(results))
