import requests

INVALID_ALIAS = 100
INVALID_BUG = 101

class BugzillaAPIError(requests.HTTPError):
    def __init__(self, bugzilla_code, *args, **kwargs):
        self.bugzilla_code = bugzilla_code
        requests.HTTPError.__init__(self, *args, **kwargs)


class BugNotFound(ValueError):
    def __init__(self, *args):
        ValueError.__init__(self, *args)
