import re
import socket
import time

from bzrest.errors import BugzillaAPIError, INVALID_ALIAS, INVALID_BUG

from dns import resolver

from paramiko import SSHClient, AuthenticationException, SSHException

from . import config
from .clients import inventory, slavealloc
from .clients.bugzilla import ProblemTrackingBug

import logging
log = logging.getLogger(__name__)


class PDU(object):
    def __init__(self, fqdn, port):
        self.fqdn = fqdn
        self.port = port

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, delay=None):
        pass

class MgmtInterface(object):
    def __init__(self, fqdn):
        self.fqdn = fqdn

    def off(self):
        pass
    def on(self):
        pass
    def powercycle(self, hard=False):
        pass


class IgnorePolicy(object):
    def missing_host_key(self, *args):
        pass

class RemoteConsole(object):
    # By trying a few different reboot commands we don't need to special case
    # different types of hosts. The "shutdown" command is for Windows, but uses
    # hyphens because it gets run through a bash shell. We also delay the
    # shutdown for a few seconds so that we have time to read the exit status
    # of the shutdown command.
    reboot_commands = ["sudo reboot", "reboot", "shutdown -f -t 3 -r"]

    def __init__(self, fqdn, credentials):
        self.fqdn = fqdn
        self.credentials = credentials
        self.connected = False
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(IgnorePolicy())

    def connect(self, timeout=30):
        last_exc = None
        for username, passwords in self.credentials.iteritems():
            for p in passwords:
                try:
                    log.info("Attempting to connect to %s as %s", self.fqdn, username)
                    self.client.connect(hostname=self.fqdn, username=username, password=p, timeout=timeout, look_for_keys=False)
                    log.info("Connection to %s succeeded!", self.fqdn)
                    self.connected = True
                    break
                # We can eat most of these exceptions because we try multiple
                # different auths. We need to hang on to it to re-raise in case
                # we ultimately fail.
                except AuthenticationException, e:
                    log.info("Authentication failure.")
                    last_exc = e
        if not self.connected:
            raise last_exc

    def disconnect(self):
        if self.connected:
            self.client.close()
        self.connected = False

    def run_cmd(self, cmd, timeout=60):
        if not self.connected:
            self.connect()

        log.debug("Running %s on %s through the shell", cmd, self.fqdn)
        try:
            shell = self._get_shell()
            shell.sendall("%s\r\necho $?\r\n" % cmd)

            time_left = timeout
            data = ""
            while True:
                while shell.recv_ready():
                    data += shell.recv(1024)

                if "echo $?" in data:
                    data = re.sub(r"\x1b[^m]*m", "", data)
                    data = re.sub(r"\x1b\[\d+;\d+f", "", data)
                    output, status = data.split("echo $?\r\n")
                    rc = int(status.split("\r\n")[0])
                    return rc, output
                else:
                    # Still waiting for the command to finish
                    if time_left <= 0:
                        shell.close()
                        raise Exception("Timed out when running command.")
                    else:
                        time_left -= 5
                        time.sleep(5)
        finally:
            self.disconnect()


    def reboot(self):
        log.info("Attempting to reboot %s", self.fqdn)

        for cmd in self.reboot_commands:
            log.debug("Trying command: %s", cmd)
            rc, output = self.run_cmd(cmd)
            if rc == 0:
                log.info("Successfully initiated reboot of %s", self.fqdn)
                # Success! We're done!
                break
            else:
                log.info("Reboot failed, rc was %d, output was:", rc)
                log.info(output)
        else:
            raise Exception("Unable to reboot %s" % self.fqdn)

    def _get_shell(self):
        shell = self.client.get_transport().open_session()
        shell.get_pty()
        shell.invoke_shell()
        # We need to sleep a little bit here to give the shell time to log in.
        # This won't work in 100% of cases, but it should be generally OK.
        time.sleep(5)
        # Once that's done we should eat whatever is in the stdout buffer so
        # that our consumer doesn't need to deal with it.
        if shell.recv_ready():
            shell.recv(1024)
        return shell

class Slave(object):
    def __init__(self, name):
        if "." not in name:
            name += "." + config["default_domain"]
        answer = resolver.query(name)
        self.name = answer.canonical_name.to_text().split(".")[0]
        self.domain = answer.canonical_name.parent().to_text().rstrip(".")
        self.ip = answer[0].to_text()
        # Per IT, parsing the FQDN is the best way to find the colo.
        # Our hostnames always end in $colo.mozilla.com.
        self.colo = self.fqdn.split(".")[-3]
        # Also per IT, the management interface (eg, IPMI), if it exists, can
        # always be found by appending "-mgmt.build.mozilla.org" to the name.
        try:
            mgmt_fqdn = "%s-mgmt.%s" % (self.name, config["default_domain"])
            resolver.query(mgmt_fqdn)
            self.mgmt = MgmtInterface(mgmt_fqdn)
        except resolver.NXDOMAIN:
            self.mgmt = None
        self.bug = None
        self.enabled = None
        self.basedir = None
        self.notes = None
        self.pdu = None

    @property
    def fqdn(self):
        return "%s.%s" % (self.name, self.domain)

    def load_slavealloc_info(self):
        log.info("Getting slavealloc debug for %s", self.name)
        debug = slavealloc.get_slave(config["slavealloc_api"], name=self.name)
        self.enabled = debug["enabled"]
        self.basedir = debug["basedir"]
        self.notes = debug["notes"]

    def load_inventory_info(self):
        log.info("Getting inventory debug for %s", self.name)
        debug = inventory.get_system(
            self.fqdn, config["inventory_api"], config["inventory_username"],
            config["inventory_password"],
        )
        if debug["pdu_fqdn"]:
            self.pdu = PDU(debug["pdu_fqdn"], debug["pdu_port"])

    def load_bug_info(self, createIfMissing=False):
        log.info("Getting bug debug for %s", self.name)
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.load()
        except BugzillaAPIError as e:
            if e.bugzilla_code in (INVALID_ALIAS, INVALID_BUG) and createIfMissing:
                log.info("Couldn't find bug for %s, creating it...", self.name)
                self.bug.create(config["bugzilla_product"], config["bugzilla_component"])
            else:
                raise

    def ssh_reboot(self):
        console = self._get_console()
        console.reboot()

    def is_alive(self, timeout=300, retry_interval=5):
        log.info("Waiting up to %d seconds for slave to revive", timeout)
        time_left = timeout
        console = self._get_console()
        while time_left > 0:
            try:
                console.connect(time_left)
                log.info("Slave is alive!")
                return True
            # Exceptions are especially common if a connection attempt
            # happens mid-shutdown. They can also be caused by transient host
            # or network issue.
            except (socket.error, SSHException):
                # We should sleep between retries to avoid spamming the host.
                log.debug("Got connection error, sleeping %d before retrying", retry_interval)
                time.sleep(retry_interval)
                time_left -= retry_interval
                if time_left <= 0:
                    log.exception("Timeout exceeded, giving up.")
                    return False

    def _get_console(self):
        return RemoteConsole(self.fqdn, config["ssh_credentials"])
