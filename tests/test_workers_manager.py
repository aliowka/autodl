from Queue import Queue

from twisted.internet.defer import Deferred, DeferredList
from twisted.trial import unittest
from service.task import Task
from service.workers_async import WorkersManager, Worker


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.counter = 0
        self.task_queue = Queue()
        self.max_tasks_number = 50
        self.bulk_size = 10
        self.deferred_tasks = []

    def _on_task_finished(self, *ignored):
        self.workers_manager.running_tasks -= 1
        self.counter += 1
        print self.counter
        if self.workers_manager.running_tasks > self.max_tasks_number:
            d = self.workers_manager.pause()
            d.addCallback(self.fire_when_ready.callback, True)
            raise Exception("MAX_TASK_NUMBER exceeded")

        if self.counter == self.bulk_size:
            d = self.workers_manager.pause()
            d.addCallback(self.fire_when_ready.callback)


    def test_workers_manager(self):

        for i in xrange(self.bulk_size):
            self.task_queue.put(Task("http://lib.ru", "aliowka", path="/tmp/autodl-test"))


        self.fire_when_ready = Deferred()

        self.workers_manager = WorkersManager(self.task_queue, self.max_tasks_number)
        self.workers_manager.on_task_finished = self._on_task_finished
        self.workers_manager.resume()

        return self.fire_when_ready

