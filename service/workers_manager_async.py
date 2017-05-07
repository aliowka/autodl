
#===============================================================================
# This is the implementation of Asynchronous Workers managed by WorkersManager.
# WorkersManager listening on the tasks_queue and once it gets the task from the queue,
# it creates a new Worker for this task and run it with runner.
# Worker is responsible for downloading and storing the result to disk.
# What's amazing here is that Worker (Task downloading and storing), together with
# WorkerManger and even the API Service itself,
# are running on a single reactor in a single thread.
# The number of workers is variable and subject to constrain of max_tasks_number.
# When the task is downloaded and saved, the Worker destroyd, but the runner continue
# to run empty. Runner is a LoopinCall which fires repeatedly. Whet it runs empty it
# increases the deleay between it's runs by (IDLE_DELAY). This is done to reduce the
# CPU load.
#===============================================================================
import os
import sys

sys.path.append(
    os.path.normpath(
        os.path.join(
            os.path.abspath(__file__),
            "..", ".."
        )
    )
)

from Queue import Empty
from twisted.internet.task import LoopingCall

from service.statistics import DownloaderStatistics
from service.settings import IDLE_DELAY
from service.workers_manager_base import BaseWorkersManager, BaseWorker
from utils.helpers import waiting_deferred

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

