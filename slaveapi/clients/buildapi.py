from calendar import timegm
from datetime import datetime
from furl import furl
from pytz import timezone, utc
import requests

import logging
log = logging.getLogger(__name__)

def get_recent_jobs(slavename, api, n_jobs=None):
    url = furl(api)
    url.path.add("recent/%s" % slavename)
    url.args["format"] = "json"
    if n_jobs:
        url.args["numbuilds"] = n_jobs
    log.debug("%s - Making request to %s", slavename, url)
    r = requests.get(str(url)).json()
    return r
