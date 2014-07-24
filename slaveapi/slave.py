from bzrest.errors import BugNotFound

from furl import furl

import socket

from .clients import slavealloc, devices
from .clients.bugzilla import ProblemTrackingBug, get_reboot_bug
from .clients.buildapi import get_recent_jobs
from .clients.ssh import SSHConsole, SSHException
from .machines.base import Machine
from .global_state import config
from .util import logException

import logging
log = logging.getLogger(__name__)

def windows2msys(path_):
    (drive, therest) = path_.split(":")
    return "/" + drive[0] + therest.replace("\\", "/")

class Slave(Machine):
    def __init__(self, name):
        Machine.__init__(self, name)
        self.bug = None
        self.reboot_bug = None
        self.enabled = None
        self.basedir = None
        self.notes = None
        self.recent_jobs = None
        self.master = None
        self.master_url = None
        self.mozpool_server = None
        # used for hosts that have a different machine running buildbot than themselves
        # Valid buildbotslave value is an instance of (or subclass thereof) the Slave class
        self.buildbotslave = None

    def load_all_info(self):
        Machine.load_all_info(self)
        self.load_slavealloc_info()
        self.load_devices_info()
        self.load_bug_info()
        self.load_recent_job_info()

    def load_slavealloc_info(self):
        log.info("Getting slavealloc info")
        info = slavealloc.get_slave(config["slavealloc_api_url"], name=self.name)
        master_info = slavealloc.get_master(config["slavealloc_api_url"], info["current_masterid"])
        self.enabled = info["enabled"]
        self.basedir = info["basedir"].rstrip("/")
        # Because we always work with UNIX style paths in SlaveAPI we need
        # to massage basedir when a Windows style one is detected.
        if self.basedir[1] == ":":
            self.basedir = windows2msys(self.basedir)
        self.notes = info["notes"]
        self.master = master_info.get("fqdn", None)
        if self.master:
            self.master_url = furl().set(scheme="http", host=self.master, port=master_info["http_port"])

    def load_inventory_info(self):
        info = Machine.load_inventory_info(self)
        if info["imaging_server"]:
            self.mozpool_server = "http://%s" % info["imaging_server"]
        # Return info to allow subclasses to do stuff with data, without refetching
        return info

    def load_devices_info(self):
        log.info("Getting devices.json info")
        device_info = devices.get_device(
            self.name, config["devices_json_url"]
        )
        if not device_info or "foopy" not in device_info or device_info["foopy"] == "None":
            return
        # Now set the buildbotslave since we have a foopy!
        self.buildbotslave = BuildbotSlave(device_info["foopy"])
        self.buildbotslave.load_all_info()

    def load_bug_info(self, createIfMissing=False):
        log.info("Getting bug info")
        self.bug = ProblemTrackingBug(self.name, loadInfo=False)
        try:
            self.bug.refresh()
            self.reboot_bug = get_reboot_bug(self)
        except BugNotFound:
            if createIfMissing:
                log.info("Couldn't find bug, creating it...")
                self.bug.create()
                self.bug.refresh()
            else:
                self.bug = None

    def load_recent_job_info(self, n_jobs=1):
        log.info("Getting recent job info")
        self.recent_jobs = get_recent_jobs(
            self.name, config["buildapi_api_url"], n_jobs=n_jobs
        )

    def to_dict(self):
        """Serializes the state of a Slave. It is up to the caller to ensure that
        any desired information (slavealloc, etc.) is loaded prior to
        serialization."""

        data = Machine.to_dict(self)
        data.update({
            "enabled": self.enabled,
            "basedir": self.basedir,
            "notes": self.notes,
            "bug": None,
            "recent_jobs": None,
            "buildbotslave": None,
            "mozpool_server": None,
        })
        if self.recent_jobs:
            data["recent_jobs"] = self.recent_jobs
        if self.bug and self.bug.data:
            data["bug"] = {
                "id": self.bug.id_,
                "is_open": self.bug.data["is_open"]
            }
        if self.buildbotslave:
            data["buildbotslave"] = self.buildbotslave.to_dict()
        if self.mozpool_server:
            data["mozpool_server"] = self.mozpool_server
        return data

class BuildbotSlave(Machine):
    # e.g. a foopy
    pass

def get_console(slave, usebuildbotslave=False):
    realslave = slave
    if usebuildbotslave:
        # Sometimes buildbot is run on different host than the slave
        # slave.basedir is still accurate, though.
        realslave = slave.buildbotslave or slave

    console = SSHConsole(realslave.ip, config["ssh_credentials"])
    try:
        console.connect()  # Make sure we can connect properly
        return console
    except (socket.error, SSHException), e:
        logException(log.error, e)
        console.disconnect() # Don't hold a connection
        return None  # No valid console
    return None  # How did we get here?
