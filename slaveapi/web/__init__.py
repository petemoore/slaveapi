from flask import Flask

from .slave import Reboot

app = Flask(__name__)

app.add_url_rule("/slave/<slave>/action/reboot", view_func=Reboot.as_view("reboot"), methods=["GET", "POST"])
