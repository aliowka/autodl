import os
import random
import string
import uuid
from urlparse import urlparse

import time
from twisted.logger import Logger
from twisted.internet.protocol import Factory

Factory.noisy = False

log = Logger()

from service.settings import ENABLE_UNIQUE_NAMES


class TASK_STATUSES:
    CREATED = "CREATED"
    ENQUEUED = "ENQUEUED"
    DOWNLOADING = "DOWNLOADING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CLEARED = "CLEARED"


class Stats(object):
    @staticmethod
    def update(task):
        if task.status[1] == TASK_STATUSES.CREATED:
            Stats.tasks_by_statuses[task.status[1]][task.task_id] = task
            return

        for group in Stats.tasks_by_statuses:
            if task.task_id in Stats.tasks_by_statuses[group]:
                Stats.tasks_by_statuses[task.status[1]][task.task_id] = task
                del Stats.tasks_by_statuses[group][task.task_id]
                break

    @staticmethod
    def get_task(task_id):

        for group in Stats.tasks_by_statuses:
            if task_id in Stats.tasks_by_statuses[group]:
                return Stats.tasks_by_statuses[group][task_id]


Stats.tasks_by_statuses = {status: {} for status in TASK_STATUSES.__dict__ if not status.startswith("_")}


class Task(object):
    def __init__(self, url, user, path=None):
        self.url = url
        self.user = user
        self.task_id = str(uuid.uuid4())
        self.full_path = self._generate_full_path(path)
        self.created = time.time()

    def _generate_full_path(self, destination):

        full_path = destination

        file_name = self._generate_file_name_from_url(self.url)
        return os.path.join(full_path, file_name)

    def _generate_file_name_from_url(self, url):
        path = urlparse(url).path
        if not path:
            file_name, file_ext = ("Unknown", "")
        else:
            file_name, file_ext = os.path.splitext(os.path.basename(url))

        if ENABLE_UNIQUE_NAMES:
            file_name = "-".join(
                [file_name, "".join([random.choice(string.ascii_letters) for _ in xrange(8)])])
        if file_ext:
            file_name = ".".join([file_name, file_ext])
        return file_name

    def update_status(self, status):
        self.status = (round(time.time() - self.created, 4), status)
        Stats.update(self)
        log.debug("%(task_id)s %(status)s %(duration)f %(url)s" % dict(
            task_id=self.task_id,
            duration=self.status[0],
            status=self.status[1],
            url=self.url))

    def __repr__(self):
        return str({"id": self.task_id,
                    "url": self.url,
                    "dest": self.full_path,
                    "status": self.status[1],
                    "duration": self.status[0]
                    })
