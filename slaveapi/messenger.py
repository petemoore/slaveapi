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
            state, item = msg[0:1]
            try:
                text = msg[2]
            except IndexError:
                text = ""
            slave, action, args, kwargs, res = item
            res.state = state
            res.text = text
