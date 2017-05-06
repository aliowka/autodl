import os

import logging
from service.task import TASK_STATUSES

log = logging.getLogger(__name__)
log.propagate = True

class BaseWorker(object):

    def _download_url_content(self, task):
        task.update_status(TASK_STATUSES.DOWNLOADING)
        log.info("Downloading URL:", str(task))

    def _save_content_to_file(self, content, task):
        log.info("Saving to disk:", str(task))
        path = task.full_path
        path_dir = os.path.dirname(path)
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        with open(path, "w+") as f:
            f.write(content)
        task.update_status(TASK_STATUSES.FINISHED)
        return task

    def process_task(self, task):
        log.info(str(task))

class BaseWorkersManager(object):

    def __init__(self, tasks_queue, max_tasks_number):
        self.running_tasks = 0
        self.max_tasks_number = max_tasks_number
        self.tasks_queue = tasks_queue
        self.running = True

    def resume(self):
        self.running = True
        log.info("Resuming workers")

    def pause(self):
        self.running = False
        log.info("Pausing workers")

    def on_task_finished(self, task):
        self.running_tasks -= 1
        log.info("Worker closed:", str(task))

    def run(self):
        raise NotImplemented()