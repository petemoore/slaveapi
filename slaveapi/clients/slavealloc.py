from furl import furl

import requests

def get_slave(api, id_=None, name=None):
    if id_ and name:
        raise ValueError("Can't retrieve slave by id and name at the same time.")

    url = furl(api)
    if id_:
        url.path = "slaves/%s" % id_
    elif name:
        url.path = "slaves/%s" % name
        url.args["byname"] = 1
    else:
        raise Exception()

    return requests.get(url).json()


def get_slaves(api, purposes=[], environs=[], pools=[], enabled=None):
    url = furl(api)
    url.path = "slaves"
    url.args["purpose"] = purposes
    url.args["environment"] = environs
    url.args["pool"] = pools
    if enabled:
        url.args["enabled"] = int(enabled)

    return requests.get(url).json()
