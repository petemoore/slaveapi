class PDU(object):
    def __init__(self, fqdn, port):
        self.fqdn = fqdn
        self.port = port

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, delay=None):
        raise NotImplementedError()

