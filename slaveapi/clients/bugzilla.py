from ..global_state import bugzilla_client


class Bug(object):
    def __init__(self, id_, loadInfo=True):
        self.id_ = id_
        self.data = {}
        if loadInfo:
            self.refresh()

    def refresh(self):
        self.data = bugzilla_client.get_bug(self.id_)
        self.id_ = self.data["id"]

    def add_comment(self, comment, data={}):
        return bugzilla_client.add_comment(self.id_, comment, data)

    def update(self, data):
        return bugzilla_client.update_bug(self.id_, data)


class ProblemTrackingBug(Bug):
    product = "Release Engineering"
    component = "Buildduty"

    def __init__(self, slave_name, *args, **kwargs):
        self.slave_name = slave_name
        self.reboot_bug = None
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


reboot_product = "Infrastructure & Operations"
reboot_component = "DCOps"
reboot_summary = "%(slave)s is unreachable"
def get_reboot_bug(slave):
    qs = "?product=%s&component=%s" % (reboot_product, reboot_component)
    qs += "&blocks=%s&resolution=---" % slave.bug.id_
    summary = reboot_summary % {"slave": slave.name}
    for bug in bugzilla_client.request("GET", "bug" + qs)["bugs"]:
        if bug["summary"] == summary:
            return Bug(bug["id"])
    else:
        return None

def file_reboot_bug(slave):
    data = {
        "product": reboot_product,
        "component": reboot_component,
        "summary": reboot_summary % {"slave": slave.name},
        "version": "other",
        "op_sys": "All",
        "platform": "All",
        "blocks": slave.bug.id_,
    }
    resp = bugzilla_client.create_bug(data)
    return Bug(resp["id"])
