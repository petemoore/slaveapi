import logging

from . import messages

log = logging.getLogger(__name__)


class Messenger(object):
    def __init__(self):
        pass

    def __call__(self):
        while True:
            state, item, text = messages.get()
            log.debug("Got message: %s", (state, item, text))
            slave, action, args, kwargs, res = item
            res.state = state
            res.text = text
