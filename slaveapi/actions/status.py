from gevent.event import Event

class ActionResult(object):
    def __init__(self, slave, action, state="pending"):
        self.id_ = id(self)
        self.slave = slave
        self.action = action
        self._state = state
        self._msg = "in progress"
        self.event = Event()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        if state == "complete":
            self.event.set()

    @property
    def msg(self):
        return self._msg

    @msg.setter
    def msg(self, msg):
        self._msg = msg

    def is_done(self):
        if self.event.isSet():
            return True
        else:
            return False

    def wait(self, timeout=None):
        return self.event.wait(timeout)
