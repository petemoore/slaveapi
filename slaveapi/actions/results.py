from collections import defaultdict

from gevent.event import Event

import time

PENDING, RUNNING, SUCCESS, FAILURE = range(4)

class ActionResult(object):
    """Contains basic information about the result of a specific Action."""
    def __init__(self, slave, action, state=PENDING,
                 request_timestamp=0,
                 start_timestamp=0,
                 finish_timestamp=0):
        self.id_ = id(self)
        self.slave = slave
        self.action = action
        self._state = state
        self._text = ""
        if not request_timestamp:
            request_timestamp = time.time()
        self._request_timestamp = request_timestamp
        self._start_timestamp = start_timestamp
        self._finish_timestamp = finish_timestamp
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

    @property
    def request_timestamp(self):
        return self._request_timestamp

    @request_timestamp.setter
    def request_timestamp(self, timestamp):
        self._request_timestamp = timestamp

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @start_timestamp.setter
    def start_timestamp(self, timestamp):
        self._start_timestamp = timestamp

    @property
    def finish_timestamp(self):
        return self._finish_timestamp

    @finish_timestamp.setter
    def finish_timestamp(self, timestamp):
        self._finish_timestamp = timestamp

    def is_done(self):
        if self.event.isSet():
            return True
        else:
            return False

    def to_dict(self, include_requestid=False):
        """Returns the state and text of this ActionResult in a dict. If
        include_requestid is True, "requestid" will also be present. Example:

        .. code-block:: python

            {
                "state": 2,
                "text": "Great success!",
                "request_timestamp": 1392414314,
                "start_timestamp": 1392414315,
                "finish_timestamp": 1392414316,
                "requestid": "234567832"
            }
        """
        data = {"state": self.state, "text": self.text,
                "request_timestamp": self._request_timestamp,
                "start_timestamp": self._start_timestamp,
                "finish_timestamp": self._finish_timestamp}
        if include_requestid:
            data["requestid"] = self.id_
        return data

    def wait(self, timeout=None):
        return self.event.wait(timeout)


def dictify_results(results):
    """Returns a dict of ActionResults broken down by slave, action, and
    requestid. Specific results are processed by
    :py:func:`slaveapi.actions.results.ActionResults.to_dict`. Example:

    .. code-block:: python

        {
            "linux-ix-slave04": {
                "reboot": {
                    "1235543252": {
                        "state": 2,
                        "text": "Great success!",
                        "request_timestamp": 1392414314,
                        "start_timestamp": 1392414315,
                        "finish_timestamp": 1392414316
                    }
                }
            },
            "w64-ix-slave05": {
                "reboot": {
                    "5748263211": {
                        "state": 3,
                        "text": "Failure :(",
                        "request_timestamp": 1392414317,
                        "start_timestamp": 1392414318,
                        "finish_timestamp": 1392414319
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
