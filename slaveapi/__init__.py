from gevent import queue

from bzrest.client import BugzillaClient

messages = queue.Queue()

config = {}
bugzilla_client = BugzillaClient()
pending = {}

from .processor import Processor
processor = Processor()
