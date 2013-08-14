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

    def off(self, hard=False):
        if hard:
            self.run_cmd("power off")
        else:
            self.run_cmd("power soft")

    def on(self):
        self.run_cmd("power on")

    def powercycle(self, delay=5):
        self.off(hard=False)
        time_left = 120
        while True:
            if "off" in self.run_cmd("power status"):
                break
            else:
                if time_left <= 0:
                    break
                time_left -= 15
                time.sleep(15)
        self.off(hard=True)
        time.sleep(5)
        self.on()

    def run_cmd(self, cmd):
        full_cmd = ["ipmitool", "-H", self.fqdn, "-I", self.interface_type,
                    "-U", self.username, "-P", self.password]
        full_cmd += cmd.split()
        return chheck_output(full_cmd, stderr=STDOUT)
