import logging

from bzrest.errors import INVALID_ALIAS, INVALID_BUG

from slaveapi import config, bugzilla_client

log = logging.getLogger(__name__)


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
            if e.bugzilla_code in (INVALID_ALIAS, INVALID_BUG) and createIfMissing:
                self.id_ = create_slave_bug(self.slave_name)
            else:
                raise


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
