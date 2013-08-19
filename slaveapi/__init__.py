from collections import defaultdict

from gevent import queue

from bzrest.client import BugzillaClient

messages = queue.Queue()

config = {}
bugzilla_client = BugzillaClient()
pending = defaultdict(dict)

from .processor import Processor
processor = Processor()
