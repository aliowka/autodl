import cgi
import json

from multiprocessing import Queue
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

from service.settings import PORT
from service.stats import Stats
from service.task import Task
from service.workers_manager import WorkersManager


class BaseView(Resource, object):
    stats = Stats()
    tasks_queue = Queue()
    workers_manager = WorkersManager()

    def render_POST(self, request):
        request.responseHeaders.addRawHeader("content-type", "application/json")

    def render_GET(self, request):
        request.responseHeaders.addRawHeader("content-type", "application/json")


class Alive(BaseView):
    isLeaf = True

    def render_GET(self, request):
        return "Hello, world! I am alive."


class AddTask(BaseView):
    isLeaf = True

    def render_POST(self, request):
        super(AddTask, self).render_POST(request)
        url = cgi.escape(request.args["url"][0])
        task = Task(url)
        self.tasks_queue.put(task)
        return json.dumps({"status": "enqueued",
                           "task_id": task.task_id,
                           "url": task.url})


class ClearTasks(BaseView):
    isLeaf = True

    def render_POST(self, request):
        super(ClearTasks, self).render_POST(request)
        tasks = []
        while not self.tasks_queue.empty():
            task = self.tasks_queue.get()
            tasks.append(task.task_id)
        return json.dumps({"status": "cleared", "tasks": tasks})


class PauseWorkers(BaseView):
    isLeaf = True

    def render_POST(self, request):
        return "Hello, world! I am located at %r." % (request.prepath,)


class ResumeWorkers(BaseView):
    isLeaf = True

    def render_POST(self, request):
        return "Hello, world! I am located at %r." % (request.prepath,)


def main():
    root = Resource()
    root.putChild('alive', Alive())
    root.putChild('add', AddTask())
    root.putChild('clear', ClearTasks())
    root.putChild('pause', PauseWorkers())
    root.putChild('resume', ResumeWorkers())

    site = Site(root)
    reactor.listenTCP(PORT, site)
    reactor.run()


if __name__ == "__main__":
    main()
