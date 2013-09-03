import re
import time

from paramiko import SSHClient, AuthenticationException

import logging
log = logging.getLogger(__name__)


class RemoteCommandError(Exception):
    def __init__(self, message, rc=None, output=None, *args, **kwargs):
        self.rc = rc
        self.output = output
        Exception.__init__(self, message, *args, **kwargs)


class IgnorePolicy(object):
    def missing_host_key(self, *args):
        pass


class SSHConsole(object):
    # By trying a few different reboot commands we don't need to special case
    # different types of hosts. The "shutdown" command is for Windows, but uses
    # hyphens because it gets run through a bash shell. We also delay the
    # shutdown for a few seconds so that we have time to read the exit status
    # of the shutdown command.
    reboot_commands = ["reboot", "sudo reboot", "shutdown -f -t 3 -r"]

    def __init__(self, fqdn, credentials):
        self.fqdn = fqdn
        self.credentials = credentials
        self.connected = False
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(IgnorePolicy())

    def connect(self, usernames=None, timeout=30):
        last_exc = None
        if usernames:
            possible_credentials = {}
            for u in usernames:
                possible_credentials[u] = self.credentials[u]
        else:
            possible_credentials = self.credentials
        for username, passwords in possible_credentials.iteritems():
            first_password = True
            for p in passwords:
                try:
                    log.debug("%s - Attempting to connect as %s", self.fqdn, username)
                    self.client.connect(hostname=self.fqdn, username=username, password=p, timeout=timeout, look_for_keys=False, allow_agent=False)
                    log.info("%s - Connection as %s succeeded!", self.fqdn, username)
                    self.connected = True
                    break
                # We can eat most of these exceptions because we try multiple
                # different auths. We need to hang on to it to re-raise in case
                # we ultimately fail.
                except AuthenticationException, e:
                    log.debug("%s - Authentication failure.", self.fqdn)
                    if first_password:
                        log.warning("%s - First password as %s didn't work.", self.fqdn, username)
                        first_password = False
                    last_exc = e
        if not self.connected:
            log.info("%s - Couldn't connect with any credentials.", self.fqdn)
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

        log.debug("%s - Running %s", self.fqdn, cmd)
        try:
            shell = self._get_shell()
            shell.sendall("%s\r\necho $?\r\n" % cmd)

            start = time.time()
            data = ""
            output = None
            rc = None
            while time.time() - start < timeout:
                while shell.recv_ready():
                    data += shell.recv(1024)

                # Once we find this in the data, we know that the command
                # has finished running. Now we have to dig around to get the
                # command output and return code.
                if "echo $?" in data:
                    # First off, we should strip any shell escape codes that
                    # may be present.
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
                    time.sleep(5)
            else:
                shell.close()
                raise RemoteCommandError("Timed out when running command.")
        except:
            log.debug("%s - Caught exception while running command:", self.fqdn, exc_info=True)
            raise RemoteCommandError("Caught exception while running command.", output=output, rc=rc)
        finally:
            self.disconnect()


    def reboot(self):
        log.info("%s - Attempting to reboot", self.fqdn)

        for cmd in self.reboot_commands:
            rc, output = self.run_cmd(cmd)
            if rc == 0:
                log.info("%s - Successfully initiated reboot", self.fqdn)
                # Success! We're done!
                return
        else:
            # XXX: raise a better exception here
            raise RemoteCommandError("Unable to reboot %s after trying all commands" % self.fqdn)

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

