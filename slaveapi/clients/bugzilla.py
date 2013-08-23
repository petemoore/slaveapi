from slaveapi import bugzilla_client


class Bug(object):
    def __init__(self, id_, loadInfo=True):
        self.id_ = id_
        self.data = {}
        if loadInfo:
            self.refresh()

    def refresh(self):
        self.data = bugzilla_client.get_bug(self.id_)

    def add_comment(self, comment, data={}):
        return bugzilla_client.add_comment(self.id_, comment, data)

    def update(self, data):
        return bugzilla_client.update_bug(self.id_, data)


class ProblemTrackingBug(Bug):
    product = "Release Engineering"
    component = "Buildduty"

    def __init__(self, slave_name, *args, **kwargs):
        self.slave_name = slave_name
        Bug.__init__(self, slave_name, *args, **kwargs)

    def create(self):
        data = {
            "product": self.product,
            "component": self.component,
            "summary": "%s problem tracking" % self.slave_name,
            "version": "other",
            "alias": self.slave_name,
            # todo: do we care about setting these correctly?
            "op_sys": "All",
            "platform": "All"
        }
        resp = bugzilla_client.create_bug(data)
        self.id_ = resp["id"]


class RebootBug(Bug):
    product = "mozilla.org"
    component = "Server Operations: DCOps"

    def __init__(self, colo, *args, **kwargs):
        self.colo = colo
        Bug.__init__(self, "reboots-%s" % colo, *args, **kwargs)

    def create(self):
        data = {
            "product": self.product,
            "component": self.component,
            "summary": "reboot requests for %s" % self.colo,
            "version": "other",
            "alias": "reboots-%s" % self.colo,
            "op_sys": "All",
            "platform": "All",
        }
        resp = bugzilla_client.create_bug(data)
        self.id_ = resp["id"]
