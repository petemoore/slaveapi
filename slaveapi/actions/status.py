from collections import defaultdict

from gevent.event import Event

PENDING, RUNNING, SUCCESS, FAILURE = range(4)

class ActionResult(object):
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

    def serialize(self, include_requestid=False):
        data = {"state": self.state, "text": self.text}
        if include_requestid:
            data["requestid"] = self.id_
        return data

    def wait(self, timeout=None):
        return self.event.wait(timeout)


def serialize_results(results):
    ret = defaultdict(lambda: defaultdict(dict))
    for slave in results:
        for action in results[slave]:
            for requestid, result in results[slave][action].iteritems():
                ret[slave][action][requestid] = result.serialize()
    return ret
