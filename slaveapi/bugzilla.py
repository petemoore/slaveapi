import logging

from bzrest.errors import INVALID_ALIAS, INVALID_BUG, BugzillaAPIError

from slaveapi import config, bugzilla_client

log = logging.getLogger(__name__)


class Bug(object):
    def __init__(self, id_, loadInfo=True):
        self.id_ = id_
        self.depends = []
        if loadInfo:
            self.load()

    def load(self):
        data = bugzilla_client.get_bug(self.id_)
        if data:
            self.depends = data.get("depends_on", [])
        return data

    def add_comment(self, comment):
        bugzilla_client.add_comment(self.id_, comment)

    def reopen(self, comment):
        data = {
            "comment": comment,
            "status": "REOPENED",
        }
        bugzilla_client.update_bug(self.id_, data)


class ProblemTrackingBug(Bug):
    def __init__(self, slave_name, loadInfo=True):
        self.slave_name = slave_name
        self.machine_state = None
        Bug.__init__(self, id_=slave_name, loadInfo=loadInfo)

    def load(self, createIfMissing=True):
        try:
            data = Bug.load(self)
            self.machine_state = data.get("machine-state", None)
        except BugzillaAPIError as e:
            if e.bugzilla_code in (INVALID_ALIAS, INVALID_BUG) and createIfMissing:
                self.create()
            else:
                raise

    def create(self):
        data = {
            "product": config["bugzilla_product"],
            "component": config["bugzilla_component"],
            "summary": "%s problem tracking" % self.slave_name,
            "version": "other",
            "alias": self.slave_name,
            # todo: do we care about setting these correctly?
            "op_sys": "All",
            "platform": "All"
        }
        resp = bugzilla_client.create_bug(data)
        self.id_ = resp["id"]
