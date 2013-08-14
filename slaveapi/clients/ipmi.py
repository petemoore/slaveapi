from subprocess import check_output, CalledProcessError, STDOUT

class IPMIInterface(object):
    interface_type = "lanplus"

    def __init__(self, fqdn, username, password):
        self.fqdn = fqdn
        self.username = username
        self.password = password

    @classmethod
    def get(cls, fqdn, username, password):
        # If this doesn't raise we can safely assume that "fqdn" has a
        # working IPMI interface.
        interface = cls(fqdn, username, password)
        try:
            interface.run_cmd("mc info")
            return interface
        except CalledProcessError:
            return None

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, hard=False):
        pass

    def run_cmd(self, cmd):
        full_cmd = ["ipmitool", "-H", self.fqdn, "-I", self.interface_type,
                    "-U", self.username, "-P", self.password]
        full_cmd += cmd.split()
        return check_output(full_cmd, stderr=STDOUT)
