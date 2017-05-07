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

from service.statistics import DownloaderStatistics
from service.exceptions import UnknownUser, CriticalParameterMissing
from service.settings import SERVICE_PORT, MAX_TASKS_NUMBER
from service.task import Task, TASK_STATUSES, Stats, TASKS
from service.workers_manager_async import WorkersManager

from twisted.python import log

from utils.helpers import timedLogFormatter

log.startLogging(sys.stdout)
log = Logger()

tasks_queue = Queue()
workers_manager = WorkersManager(tasks_queue)


class BaseView(Resource, object):
    tasks_queue = tasks_queue

    def render(self, request):
        """
        This is called for every request before any
        other render_GET or render_POST.
        
        "started" timestamp is hooked to every request
        content-type changed to application/json, since we 
        want our API allways teturn json.
        
        "username" extracted from request Authentication header,
        which means every request should be Authenticated with
        BasicAuth username and password. Password is not in use
        so might be anything.
        
        The username should be of valid user, defined
        on the service machine. It's used for writing to user's 
        home directory. 
        
        :param request: request from client
        :return: super render
        """
        request.started = time.time()
        self.username = request.getUser()
        if not self.username:
            raise Unauthorized()
        try:
            pwd.getpwnam(self.username)
        except KeyError:
            raise UnknownUser()
        request.responseHeaders.addRawHeader("content-type", "application/json")
        return super(BaseView, self).render(request)


class AddTask(BaseView):
    isLeaf = True

    def render_POST(self, request):
        """
        Handler for adding tasks. It should receive "url" and  "path"
        with the request, then the Task is created and pushed to 
        tasks_queue.
        
        :param request: request from the client
        :return: json with task
        """

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
        """
        This clears the tasks_queue. 
        :param request: 
        :return: 
        """

        while not self.tasks_queue.empty():
            task = self.tasks_queue.get()
            task.update_status(TASK_STATUSES.CLEARED)
        return json.dumps({"message": "Enqueued tasks cleared"})


class PauseWorkers(BaseView):
    isLeaf = True

    def render_GET(self, request):
        """
        This pauses workers. Id seconds in the request's
        args it passed to workers_manager and used 
        for resuming the workers after specified delay.
        
        :param request: client request
        :return: json message
        """
        seconds = request.args.get("seconds")
        seconds = int(seconds) if seconds else None
        workers_manager.pause(seconds=seconds)
        return json.dumps({"message": "Pausing Workers"})


class ResumeWorkers(BaseView):
    isLeaf = True

    def render_GET(self, request):
        """
        Resumes workers
        :param request: 
        :return: 
        """
        workers_manager.resume()
        return json.dumps({"message": "Resuming Workers"})


class TaskInfo(BaseView):
    isLeaf = True

    def render_GET(self, request):
        """
        Returns information regarding the task, specified
        with task_id as url parameter.
        :param request: 
        :return: 
        """
        if "task_id" not in request.args:
            raise CriticalParameterMissing()
        task_id = request.args["task_id"][0]
        task = TASKS.get(task_id)
        if task:
            return json.dumps({"task": str(task)})
        else:
            request.setResponseCode(404)
            return json.dumps({"message": "Not Found"})


class LastStats(BaseView):
    isLeaf = True

    def render_GET(self, request):
        """
        Returns Downloader Statistics.
        It holds counters of last 10 minutes
        for requests, aggregated by status code.
        
        :param request: 
        :return: 
        """
        dwstats = DownloaderStatistics().expiring_dict
        tasks = Stats.get_statistics()
        return json.dumps({
            "tasks": tasks,
            "downloader": dwstats
        })

class UpdateMaxTasks(BaseView):
    isLeaf = True

    def render_POST(self, request):
        """
        This handler used to update max_tasks_number limit.
        This would immediately affect the number of 
        running concurrent.
        :param request: 
        :return: 
        """
        if "max_tasks_number" not in request.args:
            raise CriticalParameterMissing()
        max_tasks_number = request.args["max_tasks_number"][0]
        workers_manager.set_max_tasks_number(int(max_tasks_number))
        return json.dumps({
            "message": "max_tasks set to %s" % workers_manager.max_tasks_number
        })

@click.command()
@click.argument('max_tasks_number', default=MAX_TASKS_NUMBER)
def main(max_tasks_number):

    # Restricting the pathes. Trying to access the path,
    # which is not listed here, would cause 404 error.
    root = BaseView()
    root.putChild('add', AddTask())
    root.putChild('clear', ClearTasks())
    root.putChild('pause', PauseWorkers())
    root.putChild('resume', ResumeWorkers())
    root.putChild('status', TaskInfo())
    root.putChild('stats', LastStats())
    root.putChild('maxtasks', UpdateMaxTasks())

    # Define the Site with custom logFormatter
    site = Site(root, logFormatter=timedLogFormatter)
    site.logRequest = True

    reactor.listenTCP(SERVICE_PORT, site)
    log.info("Starting Workers with max-tasks-number=%s" % max_tasks_number)

    workers_manager.set_max_tasks_number(max_tasks_number)
    reactor.callLater(0, workers_manager.resume)
    reactor.run()

if __name__ == "__main__":
    main()
