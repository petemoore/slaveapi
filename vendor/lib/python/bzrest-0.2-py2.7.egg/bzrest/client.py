from urlparse import urljoin

import requests

class BugzillaAPIError(requests.HTTPError):
    def __init__(self, bugzilla_code, *args, **kwargs):
        self.bugzilla_code = bugzilla_code
        requests.HTTPError.__init__(self, *args, **kwargs)


class BugzillaClient(object):
    def __init__(self, bzurl=None, username=None, password=None):
        self.configure(bzurl, username, password)

    def configure(self, bzurl, username, password):
        self.bzurl = bzurl
        if not self.bzurl.endswith("/"):
            self.bzurl += "/"
        self.username = username
        self.password = password

    def request(self, method, path, data=None):
        url = urljoin(self.bzurl, path)
        params = {
            "Bugzilla_login": self.username,
            "Bugzilla_password": self.password,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if data:
            data.json.dumps(data)
        r = requests.request(method, url, params=params, data=data, headers=headers)
        r.raise_for_status()
        # Bugzilla's REST API doesn't always return 4xx when it maybe should.
        # (Eg, loading a non-existent bug returns 200). We need to check the
        # response to know for sure whether or not there was an error.
        resp = r.json()
        if resp.get("error", False):
            raise BugzillaAPIError(resp["code"], resp["message"], response=resp)
        return resp

    def create_bug(self, data):
        return self.request("POST", "bug", data)

    def get_bug(self, id_, data=None):
        return self.request("GET", "bug/%s" % id_, data)

    def update_bug(self, id_, data):
        return self.request("POST", "bug/%s" % id_, data)
