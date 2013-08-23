from urlparse import urljoin

import requests

import logging
log = logging.getLogger(__name__)

def find_key_value(info, wanted_key):
    for key, value in [(i["key"],i["value"]) for i in info["key_value"]]:
        if key == wanted_key:
            return value
    else:
        return None

def get_system(fqdn, api, username, password):
    url = urljoin(api, "system/?format=json&hostname=%s" % fqdn)
    auth = (username, password)
    log.debug("Making request to %s", url)
    info = requests.get(url, auth=auth).json()["objects"][0]

    # We do some post processing because PDUs are buried in the key/value store
    # for some hosts.
    pdu = find_key_value(info, "system.pdu.0")
    if pdu:
        pdu, pdu_port = pdu.split(":")
        if not pdu.endswith(".mozilla.com"):
            pdu += ".mozilla.com"
        info["pdu_fqdn"] = pdu
        info["pdu_port"] = pdu_port
    else:
        info["pdu_fqdn"] = None
        info["pdu_port"] = None

    return info
