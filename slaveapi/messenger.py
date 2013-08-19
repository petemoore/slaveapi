import logging

from . import messages

log = logging.getLogger(__name__)


class Messenger(object):
    def __init__(self):
        pass

    def __call__(self):
        while True:
            msg = messages.get()
            log.debug("Got message: %s", msg)
            slave, action, args, kwargs, res = msg[1]
            res.state = "complete"
            res.msg = msg[0]
