from urlparse import urljoin

import requests

def get_slave(api, id_=None, name=None):
    if id_ and name:
        raise ValueError("Can't retrieve slave by id and name at the same time.")

    if id_:
        url = urljoin(api, "slaves/%s" % id_)
    elif name:
        url = urljoin(api, "slaves/%s?byname=1" % name)
    else:
        raise Exception()

    return requests.get(url).json()
