class IPMIInterface(object):
    interface_type = "lanplus"

    def __init__(self, fqdn):
        self.fqdn = fqdn

    @staticmethod
    def exists(fqdn):
        pass

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, hard=False):
        pass


