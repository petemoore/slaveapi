import gevent

import logging
log = logging.getLogger(__name__)

def reboot(slave):
    log.debug("imma rebooot!")
    gevent.sleep(5)
    log.debug("i rebooteded!")
