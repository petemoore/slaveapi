import re
import time
import socket

from paramiko import SSHClient, AuthenticationException, SSHException

import logging

from ..util import logException
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
    # Best guess at the maximum possible width of any shell prompt we encounter.
    # This needs to be tracked because we run commands through a pty, and if
    # len(prompt) + len(cmd) is more than the pty width, a newline will show up
    # in the output partway through the command. This is really far from ideal
    # but until we can run commands through ssh "exec" instead of a pty, we're
    # stuck with it.
    max_prompt_size = 100

    def __init__(self, fqdn, credentials, pty_width=1000):
        self.fqdn = fqdn
        self.credentials = credentials
        self.pty_width = pty_width
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
                    log.debug("Attempting to connect as %s", username)
                    self.client.connect(hostname=self.fqdn, username=username, password=p, timeout=timeout, look_for_keys=False, allow_agent=False)
                    log.info("Connection as %s succeeded!", username)
                    self.connected = True
                    # Nothing else to do, easiest just to return here rather
                    # than break out of two loops.
                    return
                # We can eat most of these exceptions because we try multiple
                # different auths. We need to hang on to it to re-raise in case
                # we ultimately fail.
                except AuthenticationException, e:
                    log.debug("Authentication failure.")
                    if first_password:
                        log.warning("First password as %s didn't work.", username)
                        first_password = False
                    last_exc = e
                except socket.error, e:
                    # Exit out early if there is a socket error, such as:
                    # ECONNREFUSED (Connection Refused). These errors are
                    # typically raised at the OS level.
                    from errno import errorcode
                    log.debug("Socket Error (%s) - %s", errorcode[e[0]], e[1])
                    last_exc = e
                    break
        if not self.connected:
            log.info("Couldn't connect with any credentials.")
            raise last_exc

    def disconnect(self):
        if self.connected:
            self.client.close()
        self.connected = False
    
    def __del__(self):
        self.disconnect()

    def run_cmd(self, cmd, timeout=60):
        """Runs a command on the remote console. In order to support weird SSH
           servers that don't support "exec", we do this through a pty and
           shell, which makes it more complicated than it needs to be. Rather
           than letting the SSH server deal with retrieving the return code,
           we need to get it through the shell by parsing $?."""
        if (len(cmd) + self.max_prompt_size) > self.pty_width:
            raise ValueError("Command '%s' exceeds pty width, cannot run it." % cmd)

        if not self.connected:
            self.connect()

        log.debug("Running %s", cmd)
        try:
            output = None
            rc = None
            shell = self._get_shell()
            shell.sendall("%s\r\necho $?\r\n" % cmd)

            start = time.time()
            data = ""
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
            logException(log.debug, "Caught exception while running command:")
            raise RemoteCommandError("Caught exception while running command.", output=output, rc=rc)
        finally:
            self.disconnect()


    def reboot(self):
        log.info("Attempting to reboot")

        for cmd in self.reboot_commands:
            rc, output = self.run_cmd(cmd)
            if rc == 0:
                log.info("Successfully initiated reboot")
                # Success! We're done!
                return
        else:
            # XXX: raise a better exception here
            raise RemoteCommandError("Unable to reboot %s after trying all commands" % self.fqdn)

    def _get_shell(self, timeout=180):
        shell = self.client.get_transport().open_session()
        shell.get_pty(width=self.pty_width)
        shell.invoke_shell()
        # Even after the SSH connection is made, some shells may take awhile
        # to launch (see bug 943508 for an example). Because of this, we
        # need to verify that the shell is ready before returning. We can use
        # a magic string ("SHELL_READY") to do this -- once we see it in the
        # output, we know the shell is responsive. It may look a little strange
        # to send this in each iteration of the loop but because we're waiting
        # on the shell to be ready we can't rely on any characters we send to
        # be buffered - we need to resend them over and over.
        for i in range(timeout/2):
            shell.sendall("\r\necho SHELL_READY\r\n")
            data = ""
            time.sleep(1)
            while shell.recv_ready():
                data += shell.recv(1024)
            if "SHELL_READY" in data:
                return shell
            else:
                time.sleep(1)
        else:
            raise RemoteCommandError("Shell never became ready.")
