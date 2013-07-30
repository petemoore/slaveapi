import json
import logging
from urlparse import urljoin

import grequests
from requests.exceptions import HTTPError

from slaveapi import config

log = logging.getLogger(__name__)


bad_alias_code = 100
bad_bug_code = 101

class BugzillaAPIError(HTTPError):
    def __init__(self, bugzilla_code, *args, **kwargs):
        self.bugzilla_code = bugzilla_code
        HTTPError.__init__(self, *args, **kwargs)


class Bug(object):
    def __init__(self, id_, loadInfo=True):
        self.id_ = id_
        self.depends = []
        if loadInfo:
            self.load()

    def load(self):
        data = load_bug(self.id_)
        if data:
            self.depends = data.get("depends_on", [])
        return data


class ProblemTrackingBug(Bug):
    def __init__(self, slave_name, loadInfo=True):
        self.slave_name = slave_name
        self.machine_state = None
        Bug.__init__(self, id_=slave_name, loadInfo=loadInfo)

    def load(self, createIfMissing=False):
        try:
            data = Bug.load(self)
            self.machine_state = data.get("machine-state", None)
        except BugzillaAPIError as e:
            if e.bugzilla_code in (bad_alias_code, bad_bug_code) and createIfMissing:
                self.id_ = create_slave_bug(self.slave_name)
            else:
                raise


def bugzilla_request(method, url, data=None):
    url = urljoin(config["bugzilla_api"], url)
    params = {
        "Bugzilla_login": config["bugzilla_username"],
        "Bugzilla_password": config["bugzilla_password"],
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if data:
        data = json.dumps(data)
    r = grequests.request(method, url, params=params, data=data, headers=headers).send()
    r.raise_for_status()
    # Bugzilla's REST API doesn't always return 4xx when it maybe should.
    # (Eg, loading a non-existent bug returns 200). We need to check the
    # response to know for sure whether or not there was an error.
    resp = r.json()
    if resp.get("error", False):
        raise BugzillaAPIError(resp["code"], resp["message"], response=resp)
    return resp


def load_bug(id_):
    resp = bugzilla_request("GET", "bug/%s" % id_)
    return resp["bugs"][0]


def create_slave_bug(slave_name):
    data = {
        "product": config["bugzilla_product"],
        "component": config["bugzilla_component"],
        "summary": "%s problem tracking" % slave_name,
        "version": "other",
        # todo: do we care about setting these correctly?
        "op_sys": "All",
        "platform": "All"
    }
    resp = bugzilla_request("POST", "bug", data=data)
    return resp["id"]


def add_comment():
    pass

def get_reboot_bug(create=False):
    pass
