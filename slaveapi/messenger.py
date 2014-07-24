import logging

from .global_state import messages, log_data

log = logging.getLogger(__name__)


class Messenger(object):
    def __init__(self):
        pass

    def __call__(self):
        # use "-M-" for messenger as our "slave"
        log_data.slave = "-M-"
        while True:
            msg = messages.get()
            log.debug("Got message: %s", msg)
            state, item = msg[0:2]
            try:
                text = msg[2]
            except IndexError:
                text = ""
            try:
                start_ts = msg[3]
            except IndexError:
                start_ts = 0
            try:
                finish_ts = msg[4]
            except IndexError:
                finish_ts = 0
            slave, action, args, kwargs, res = item
            res.state = state
            res.text = text
            res.start_timestamp = start_ts
            res.finish_timestamp = finish_ts
