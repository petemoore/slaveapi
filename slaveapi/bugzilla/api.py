from slaveapi import bugzilla_client, config

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
        # catch something more specifi here
        except:
            if createIfMissing:
                self.id_ = create_slave_bug(self.slave_name)
            else:
                raise


def load_bug(id_):
    resp = bugzilla_client.Bug.get(dict(ids=[id_]))
    return resp["bugs"][0]


def create_slave_bug(slave_name):
    data = {
        "product": config["bugzilla_product"],
        "component": config["bugzilla_component"],
        "summary": "%s problem tracking" % slave_name,
        "version": "other",
        "alias": slave_name,
        # todo: do we care about setting these correctly?
        "op_sys": "All",
        "platform": "All"
    }
    resp = bugzilla_client.Bug.create(data)
    return resp["id"]


def add_comment():
    pass

def get_reboot_bug(create=False):
    pass
