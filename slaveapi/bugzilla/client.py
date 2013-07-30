import xmlrpclib

from pyzilla import BugZilla, CookieAuthXMLRPCTransport


class BugzillaClient(BugZilla):
    """Thin wrapper for pyzilla that allows runtime-configuration."""
    def __init__(self, url=None, *args, **kwargs):
        if url:
            self.configure(url, *args, **kwargs)

    def configure(self, url, *args, **kwargs):
        xmlrpclib.Server.__init__(self, url, CookieAuthXMLRPCTransport(*args, **kwargs))
