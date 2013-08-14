import re
import time

from paramiko import SSHClient, AuthenticationException

import logging
log = logging.getLogger(__name__)


class IgnorePolicy(object):
    def missing_host_key(self, *args):
        pass

class SSHConsole(object):
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
        """Runs a command on the remote console. In order to support weird SSH
           servers that don't support "exec", we do this through a pty and
           shell, which makes it more complicated than it needs to be. Rather
           than letting the SSH server deal with retrieving the return code,
           we need to get it through the shell by parsing $?."""
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

                # Once we find this in the data, we know that the command
                # has finished running. Now we have to dig around to get the
                # command output and return code.
                if "echo $?" in data:
                    # First off, we should strip any shell escape codes that
                    # may be present.
                    data = re.sub(r"\x1b[^m]*m", "", data)
                    data = re.sub(r"\x1b\[\d+;\d+f", "", data)
                    # Then we need to roughly split up the output and return
                    # code portions.
                    output, status = data.split("echo $?\r\n")
                    # The output needs lots of massaging to get right.
                    # First we need to strip away everything up to and
                    # including the echoing of the command we just ran.
                    output = output.split("%s" % cmd)[1]
                    # Then we strip away the new prompt that appeared after
                    # the command was run.
                    output = output.split("\r\n")[:-2]
                    # Finally, join the output back together into a useful
                    # string.
                    output = "\n".join(output)
                    # The return code is much easier -- we just want whatever
                    # was on the first line of the output of "echo $?".
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
        shell.sendall("clear\r\n")
        # We need to sleep a little bit here to give the shell time to log in.
        # This won't work in 100% of cases, but it should be generally OK.
        time.sleep(5)
        # Once that's done we should eat whatever is in the stdout buffer so
        # that our consumer doesn't need to deal with it.
        if shell.recv_ready():
            shell.recv(1024)
        return shell

