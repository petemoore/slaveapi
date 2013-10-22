from collections import defaultdict

from gevent.event import Event

PENDING, RUNNING, SUCCESS, FAILURE = range(4)

class ActionResult(object):
    """Contains basic information about the result of a specific Action."""
    def __init__(self, slave, action, state=PENDING):
        self.id_ = id(self)
        self.slave = slave
        self.action = action
        self._state = state
        self._text = ""
        self.event = Event()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in (PENDING, RUNNING, SUCCESS, FAILURE):
            raise ValueError("Invalid state: %s" % state)
        self._state = state
        if state in (SUCCESS, FAILURE):
            self.event.set()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    def is_done(self):
        if self.event.isSet():
            return True
        else:
            return False

    def to_dict(self, include_requestid=False):
        """Returns the state and text of this ActionResult in a dict. If
        include_requestid is True, "requestid" will also be present. Example::

            {
                "state": 2,
                "text": "Great success!",
                "requestid": "234567832"
            }
        """
        data = {"state": self.state, "text": self.text}
        if include_requestid:
            data["requestid"] = self.id_
        return data

    def wait(self, timeout=None):
        return self.event.wait(timeout)


def dictify_results(results):
    """Returns a dict of ActionResults broken down by slave, action, and
    requestid. Specific results are processed by
    :py:func:`slaveapi.actions.results.ActionResults.to_dict`. Example::

        {
            "linux-ix-slave04": {
                "reboot": {
                    "1235543252": {
                        "state": 2,
                        "text": "Great success!"
                    }
                }
            },
            "w64-ix-slave05": {
                "reboot": {
                    "5748263211": {
                        "state": 3,
                        "text": "Failure :("
                    }
                }
            }
        }
    """
    ret = defaultdict(lambda: defaultdict(dict))
    for slave in results:
        for action in results[slave]:
            for requestid, result in results[slave][action].iteritems():
                ret[slave][action][requestid] = result.to_dict()
    return ret
