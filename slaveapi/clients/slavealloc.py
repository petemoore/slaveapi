from furl import furl

import requests
from requests import RequestException
import json

import logging
from ..actions.results import FAILURE, SUCCESS

log = logging.getLogger(__name__)

def get_slave(api, id_=None, name=None):
    if id_ and name:
        raise ValueError("Can't retrieve slave by id and name at the same time.")

    url = furl(api)
    if id_:
        url.path.add("slaves/%s" % id_)
    elif name:
        url.path.add("slaves/%s" % name)
        url.args["byname"] = 1
    else:
        raise Exception()

    log.info("Making request to: %s", url)
    return requests.get(str(url)).json()

def get_slave_id(api, name):
    return get_slave(api, name=name)['slaveid']

def update_slave(api, name, data):
    """
    updates a slave's values in slavealloc.

    :param api: the api url for slavealloc
    :type api: str
    :param name: hostname of slave
    :type name: str
    :param data: values to be updated
    :type data: dict

    :rtype: tuple
    """

    return_msg = "Updating slave %s in slavealloc..." % name
    id_ = get_slave_id(api, name=name)

    url = furl(api)
    url.path.add("slaves/%s" % id_)
    payload = json.dumps(data)

    try:
        response = requests.put(str(url), data=payload)
    except RequestException as e:
        log.exception("%s - Caught exception while updating slavealloc.", name)
        log.exception("Exception message: %s" % e)
        return_msg += "Failed\nCaught exception while updating: %s" % (e,)
        return FAILURE, return_msg

    if response.status_code == 200:
        return_msg += "Success"
        return_code = SUCCESS
    else:
        return_msg += "Failed\n"
        return_msg += 'error response code: %s\n' % response.status_code
        return_msg += 'error response msg: %s' % response.reason
        return_code = FAILURE

    return return_code, return_msg

def get_slaves(api, purposes=[], environs=[], pools=[], enabled=None):
    url = furl(api)
    url.path.add("slaves")
    url.args["purpose"] = purposes
    url.args["environment"] = environs
    url.args["pool"] = pools
    if enabled:
        url.args["enabled"] = int(enabled)

    log.info("Making request to: %s", url)
    return requests.get(str(url)).json()


def get_master(api, id_):
    url = furl(api)
    url.path.add("masters/%s" % id_)
    return requests.get(str(url)).json()
