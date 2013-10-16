from urlparse import urljoin

import requests

import logging
log = logging.getLogger(__name__)

def get_recent_jobs(slavename, api, n_jobs=None):
    url = urljoin(api, "recent/%s?format=json" % slavename)
    if n_jobs:
        url += "&numbuilds=%s" % n_jobs
    log.debug("%s - Making request to %s", slavename, url)
    print url
    return requests.get(url).json()
