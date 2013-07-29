import logging
from urlparse import urljoin

import grequests

from slaveapi import config

log = logging.getLogger(__name__)

class Bug(object):
    def __init__(self, id_, loadInfo=True):
        self.id_ = int(id_)
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

    def load(self, createIfMissing=True):
        data = Bug.load(self)
        if not data:
            if createIfMissing:
                self.id_ = self.create_slave_bug(self.slave_name)
        else:
            self.machine_state = data.get("machine-state", None)


def load_bug(self, id_):
    url = urljoin(config["bugzilla_api"], "bug/%d" % self.id_)
    r = grequests.get(url).send().json()
    if r.ok:
        return r.json()["bugs"][0]
    else:
        log.error("Unable to retrieve bug info for %d", self.id_)
        log.debug("Response was %d: %s", r.status_code, r.text)
        # todo: probably should raise an exception here
        return None


def add_comment():
    pass

def create_slave_bug():
    pass

def get_reboot_bug(create=False):
    pass
