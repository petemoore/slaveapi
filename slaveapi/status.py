class ActionStatus(object):
    def __init__(self, state="pending"):
        self.state = state
        self.result = ""

    @property
    def state(self):
        return self.state

    @state.setter
    def state(self, state):
        self.state = state

    @property
    def result(self):
        return self.result

    @result.setter
    def result(self, result):
        self.result = result
