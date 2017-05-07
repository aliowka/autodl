# -*- coding: utf-8 -*-
import os
import requests
import shutil
from multiprocessing import Pool
from service.workers_manager_base import BaseWorker, BaseWorkersManager


class Worker(BaseWorker):

    def _download_url_content(self, task):
        super(Worker, self)._download_url_content()
        return requests.get(task.url).text

    def process_task(self, task):
        super(Worker, self).process_task(task)
        content = self._download_url_content(task)
        self._save_content_to_file(content, task)


class WorkersManager(BaseWorkersManager):

    def __init__(self, tasks_queue, max_tasks_number):

        self.max_tasks_number = max_tasks_number
        self.tasks_queue = tasks_queue
        self.running = True

    def run(self):
        pool = Pool(10)

        while True:
            task = self.tasks_queue.get_nowait()
            print pool.apply_async(Worker().process_task, (task,))

if __name__ == '__main__':
    path = "/tmp/test2"
    if os.path.exists(path):
        shutil.rmtree(path)
    wm =WorkersManager()
    wm.run()
