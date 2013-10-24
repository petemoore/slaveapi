from flask import Flask

from .results import Results
from .slave import Reboot, Slave
from .slaves import Slaves

app = Flask(__name__)

app.add_url_rule("/results", view_func=Results.as_view("results"), methods=["GET"])
app.add_url_rule("/slaves", view_func=Slaves.as_view("slaves"), methods=["GET"])
app.add_url_rule("/slaves/<slave>", view_func=Slave.as_view("slave"), methods=["GET"])
app.add_url_rule("/slaves/<slave>/actions/reboot", view_func=Reboot.as_view("reboot"), methods=["GET", "POST"])
