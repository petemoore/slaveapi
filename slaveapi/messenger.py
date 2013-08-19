import logging

from . import messages, status

log = logging.getLogger(__name__)


class Messenger(object):
    def __init__(self):
        pass

    def __call__(self):
        while True:
            msg = messages.get()
            log.debug("Got message: %s", msg)
            slave, action, args, kwargs, s = msg[1]
            s.state = "complete"
            s.result = msg[0]
