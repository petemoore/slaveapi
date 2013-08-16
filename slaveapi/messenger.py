import logging

from . import messages, pending

log = logging.getLogger(__name__)


class Messenger(object):
    def __init__(self):
        pass

    def __call__(self):
        while True:
            msg = messages.get()
            log.debug("Got message: %s", msg)
            slave, action, args, kwargs, e = msg[1]
            try:
                if msg[0] == "done":
                    pass # success!
                elif msg[0] == "error":
                    pass # boo!
            except:
                log.exception("Failed to process message: %s", msg)
            finally:
                try:
                    del pending[(slave, action.__name__)]
                except KeyError:
                    log.info("WEIRD: Couldn't delete pending event found for message: %s", msg)
