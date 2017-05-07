import cgi
import json

import pwd
from Queue import Queue

import click
import sys

import time
from twisted.cred.error import Unauthorized
from twisted.internet import reactor
from twisted.logger import Logger
from twisted.web.resource import Resource
from twisted.web.server import Site

from service.downloader_statistics import DownloaderStatistics
from service.exceptions import UnknownUser, CriticalParameterMissing
from service.settings import SERVICE_PORT, MAX_TASKS_NUMBER
from service.task import Task, TASK_STATUSES, Stats
from service.workers_async import WorkersManager

from twisted.python import log

from utils.helpers import timedLogFormatter

log.startLogging(sys.stdout)
log = Logger()

tasks_queue = Queue()
workers_manager = WorkersManager(tasks_queue)


class BaseView(Resource, object):
    tasks_queue = tasks_queue

    def render(self, request):
        request.started = time.time()
        self.username = request.getUser()
        if not self.username:
            raise Unauthorized()
        try:
            pwd.getpwnam(self.username)
        except KeyError:
            raise UnknownUser()

        return super(BaseView, self).render(request)

    def render_POST(self, request):
        request.responseHeaders.addRawHeader("content-type", "application/json")

    def render_GET(self, request):
        request.responseHeaders.addRawHeader("content-type", "application/json")


class AddTask(BaseView):
    isLeaf = True

    def render_POST(self, request):
        super(AddTask, self).render_POST(request)

        if "url" not in request.args:
            raise CriticalParameterMissing()

        if "path" not in request.args:
            raise CriticalParameterMissing()

        url = cgi.escape(request.args["url"][0])
        path = request.args.get("path", [None])[0]
        task = Task(url, self.username, path)
        task.update_status(TASK_STATUSES.ENQUEUED)
        tasks_queue.put(task)
        return json.dumps({"task": str(task)})


class ClearTasks(BaseView):
    isLeaf = True

    def render_GET(self, request):
        super(ClearTasks, self).render_POST(request)

        while not self.tasks_queue.empty():
            task = self.tasks_queue.get()
            task.update_status(TASK_STATUSES.CLEARED)
        return json.dumps({"message": "Enqueued tasks cleared"})


class PauseWorkers(BaseView):
    isLeaf = True

    def render_GET(self, request):
        seconds = request.args.get("seconds")
        seconds = int(seconds) if seconds else None
        workers_manager.pause(seconds=seconds)
        return json.dumps({"message": "Pausing Workers"})


class ResumeWorkers(BaseView):
    isLeaf = True

    def render_GET(self, request):
        workers_manager.resume()
        return json.dumps({"message": "Resuming Workers"})


class TaskInfo(BaseView):
    isLeaf = True

    def render_GET(self, request):
        if "task_id" not in request.args:
            raise CriticalParameterMissing()
        task_id = request.args["task_id"][0]
        task = Stats.get_task(task_id)
        if task:
            return json.dumps({"task": str(task)})
        else:
            request.setResponseCode(404)
            return json.dumps({"message": "Not Found"})


class LastStats(BaseView):
    isLeaf = True

    def render_GET(self, request):
        dwstats = DownloaderStatistics().expiring_dict
        tasks = Stats.get_statistics()
        return json.dumps({
            "tasks": tasks,
            "downloader": dwstats
        })


@click.command()
@click.argument('max_tasks_number', default=MAX_TASKS_NUMBER)
def main(max_tasks_number):
    root = BaseView()
    root.putChild('add', AddTask())
    root.putChild('clear', ClearTasks())
    root.putChild('pause', PauseWorkers())
    root.putChild('resume', ResumeWorkers())
    root.putChild('status', TaskInfo())
    root.putChild('stats', LastStats())

    site = Site(root, logFormatter=timedLogFormatter)
    site.logRequest = True

    reactor.listenTCP(SERVICE_PORT, site)
    log.info("Starting Workers with max-tasks-number=%s" % max_tasks_number)

    workers_manager.set_max_tasks_number(max_tasks_number)
    reactor.callLater(0, workers_manager.resume)
    reactor.run()

if __name__ == "__main__":
    main()
