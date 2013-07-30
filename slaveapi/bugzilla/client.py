import xmlrpclib

from pyzilla import BugZilla, CookieAuthXMLRPCTransport


class BugzillaClient(BugZilla):
    """Thin wrapper for pyzilla that allows runtime-configuration."""
    def __init__(self, url=None, verbose=False, cookiefile=None, user_agent=None):
        if url:
            self.configure(url, verbose, cookiefile, user_agent)

    def configure(self, url, verbose=False, cookiefile=None, user_agent=None):
        xmlrpclib.Server.__init__(self,
            url,
            CookieAuthXMLRPCTransport(cookiefile=cookiefile, user_agent=user_agent),
            verbose=verbose
        )
