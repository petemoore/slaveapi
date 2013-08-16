import logging

from gevent import queue, spawn
from gevent.event import Event

from . import messages

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
        e = Event()
        item = (slave, action, args, kwargs, e)
        log.debug("Adding work to queue: %s", item)
        self.work_queue.put(item)
        self._start_worker()
        return e

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
            e = None
            try:
                jobs += 1
                try:
                    item = self.work_queue.get(block=False)
                    if not item:
                        break
                except queue.Empty:
                    break

                log.debug("Processing item: %s", item)
                slave, action, args, kwargs, e = item
                action(slave, *args, **kwargs)

                messages.put(("done", item))

                # todo, bail after max jobs
                if jobs >= self.max_jobs:
                    break
            except:
                log.exception("Something went wrong while processing!")
                if item:
                    log.exception("Item was: %s", item)
                messages.put(("error", item))
            finally:
                if e:
                    e.set()
