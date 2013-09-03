from flask import Flask

from .results import Results
from .slave import Reboot

app = Flask(__name__)

app.add_url_rule("/results", view_func=Results.as_view("results"), methods=["GET"])
app.add_url_rule("/slave/<slave>/action/reboot", view_func=Reboot.as_view("reboot"), methods=["GET", "POST"])
