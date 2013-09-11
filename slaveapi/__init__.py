__version_info__ = ("1", "0")
__version__ = ".".join(__version_info__)

from collections import defaultdict

from gevent import queue

from bzrest.client import BugzillaClient

messages = queue.Queue()

config = {}
bugzilla_client = BugzillaClient()
results = defaultdict(lambda: defaultdict(dict))

from .processor import Processor
processor = Processor()

from .messenger import Messenger
messenger = Messenger()
