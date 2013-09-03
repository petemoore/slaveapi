from flask import jsonify
from flask.views import MethodView

from .. import results
from ..actions.status import serialize_results


class Results(MethodView):
    def get(self):
        return jsonify(serialize_results(results))
