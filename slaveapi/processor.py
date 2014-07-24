import logging
import time

from gevent import queue, spawn

from .actions.results import ActionResult, RUNNING, FAILURE
from .global_state import messages

log = logging.getLogger(__name__)


class Processor(object):
    max_jobs = 20

    def __init__(self):
        self._message_loop = None
        self.stopped = False
        self.workers = []
        self.work_queue = queue.Queue()

    def configure(self, concurrency):
        self.concurrency = concurrency

    def add_work(self, slave, action, *args, **kwargs):
        res = ActionResult(slave, action.__name__)
        item = (slave, action, args, kwargs, res)
        log.debug("%s - Adding work to queue: %s", slave, item)
        self.work_queue.put(item)
        self._start_worker()
        return res

    def _start_worker(self):
        if len(self.workers) < self.concurrency:
            log.debug("Spawning new worker")
            t = spawn(self._worker)
            t.link(self._worker_done)
            self.workers.append(t)

    def _worker_done(self, t):
        self.workers.remove(t)
        if self.work_queue.qsize() and not self.stopped:
            self._start_worker()

    def _worker(self):
        jobs = 0
        while True:
            try:
                jobs += 1
                try:
                    item = self.work_queue.get(block=False)
                    if not item:
                        break
                except queue.Empty:
                    break

                log.debug("Processing item: %s", item)
                slave, action, args, kwargs, res = item
                start_ts = time.time()
                messages.put((RUNNING, item, start_ts))
                res, msg = action(slave, *args, **kwargs)
                finish_ts = time.time()

                messages.put((res, item, msg, start_ts, finish_ts))

                # todo, bail after max jobs
                if jobs >= self.max_jobs:
                    break
            except Exception, e:
                log.exception("Something went wrong while processing!")
                if item:
                    log.debug("Item was: %s", item)
                messages.put((FAILURE, item, str(e)))
