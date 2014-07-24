import requests

import logging
log = logging.getLogger(__name__)

def get_device(name, url):
    log.debug("Requesting %s", url)
    all_devices = requests.get(url).json()
    if name in all_devices:
        return all_devices[name]
    return None
