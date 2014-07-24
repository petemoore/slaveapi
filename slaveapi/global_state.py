from collections import defaultdict

from gevent import queue
from gevent import local

from bzrest.client import BugzillaClient

log_data = local.local()

messages = queue.Queue()

config = {}
bugzilla_client = BugzillaClient()
results = defaultdict(lambda: defaultdict(dict))

from .processor import Processor
processor = Processor()

from .messenger import Messenger
messenger = Messenger()

semaphores = {}
