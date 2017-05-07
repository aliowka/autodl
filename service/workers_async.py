import os
import sys
from Queue import Empty, Queue
import shutil

from twisted.internet.task import LoopingCall

from service.downloader_statistics import DownloaderStatistics
from service.settings import IDLE_DELAY
from service.task import Task
from service.workers_base import BaseWorkersManager, BaseWorker
from service.workers_multiproc import WorkersManager
from utils.helpers import waiting_deferred

sys.path.append(
    os.path.normpath(
        os.path.join(
            os.path.abspath(__file__),
            "..", ".."
        )
    )
)

from twisted.internet import reactor
from twisted.web.client import Agent, readBody


class Worker(BaseWorker):
    generate_uniq_name = True

    def _download_url_content(self, task):
        super(Worker, self)._download_url_content(task)
        agent = Agent(reactor)
        d = agent.request(method="GET", uri=task.url)
        d.addBoth(DownloaderStatistics.update)
        d.addCallback(readBody)
        return d

    def process_task(self, task):
        super(Worker, self).process_task(task)
        d = self._download_url_content(task)
        d.addCallback(self._save_content_to_file, task)
        return d


class WorkersManager(BaseWorkersManager):
    runners = []

    def resume(self):
        for i in xrange(self.max_tasks_number):
            runner = LoopingCall(self.run)
            if runner.running:
                continue
            self.runners.append(runner)
            runner.start(0.1)


    def pause(self, seconds=None):
        for runner in self.runners:
            if runner.running:
                runner.stop()

        if seconds:
            reactor.callLater(seconds, self.resume)

    def idle(self):
        pass

    def on_task_finished(self, task):
        super(WorkersManager, self).on_task_finished(task)
        if self.running_tasks == 0:
            self.idle()

    def run(self):
        if self.running_tasks < self.max_tasks_number:
            try:
                task = self.tasks_queue.get_nowait()
                self.running_tasks += 1
                worker = Worker()
                d = worker.process_task(task)
                d.addBoth(self.on_task_finished)
                return d
            except Empty:
                pass

        return waiting_deferred(reactor, IDLE_DELAY)


if __name__ == '__main__':
    q = Queue()
    wm = WorkersManager(q)
    path = "/tmp/test1"
    if os.path.exists(path):
        shutil.rmtree(path)

    for i in xrange(100):
        task = Task("http://lib.ru", "aliowka", path)
        q.put(task)
    reactor.callLater(0, wm.resume)
    # reactor.callLater(10, wm.pause)
    # reactor.callLater(20, wm.resume)
    reactor.run()
