from calendar import timegm
from datetime import datetime
from furl import furl
from pytz import timezone, utc
import requests
from ..global_state import semaphores

import logging
log = logging.getLogger(__name__)

def get_recent_jobs(slavename, api, n_jobs=None):
    log.debug("Aquiring buildapi semaphore")
    with semaphores["buildapi"]:
        log.debug("Aquired buildapi semaphore")
        url = furl(api)
        url.path.add("recent/%s" % slavename)
        url.args["format"] = "json"
        if n_jobs:
            url.args["numbuilds"] = n_jobs
        log.debug("Making request to %s", url)
        r = requests.get(str(url)).json()
        return r
