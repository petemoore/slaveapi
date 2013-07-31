from urlparse import urljoin

import requests

from . import config

def get_slave(id_=None, name=None):
    if id_ and name:
        raise ValueError("Can't retrieve slave by id and name at the same time.")

    if id_:
        url = urljoin(config["slavealloc_api"], "slaves/%s" % id_)
    elif name:
        url = urljoin(config["slavealloc_api"], "slaves/%s?byname=1" % name)
    else:
        raise Exception()

    return requests.get(url).json()
