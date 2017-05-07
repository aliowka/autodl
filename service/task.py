import json
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
    def update(prev_status, new_status):
        """
        Stats.tasks_by_statuses represents tasks counters 
        aggregated by tasks statuses:
        
        { "CREATED": int, 
          "ENQUEUED": int, 
          "DOWNLOADING": int, 
          "FINISHED": int, 
          "FAILED":int, 
          "CLEARED":int}
        
        When task changes it's status from previous to new  
        the statistics should follow the change as well.
        The counter of previous status should be decreased
        and the counter of new - increased.
        
        
        :return: 
        """
        if new_status == TASK_STATUSES.CREATED:
            Stats.tasks_statuses_counters[new_status] += 1
            return

        Stats.tasks_statuses_counters[new_status] += 1
        Stats.tasks_statuses_counters[prev_status] -=1

    @staticmethod
    def get_statistics():
        """
        :return: statistic
        """
        return Stats.tasks_statuses_counters

    @staticmethod
    def get_task(task_id):

        """
        Returns task by task_id
        :param task_id: GUID
        :return: 
        """
        return Stats.tasks_by_id[task_id]

# Initialise Stats.tasks_by_statuses to {"CREATED": 0, ...}
Stats.tasks_statuses_counters = {status: 0 for status in TASK_STATUSES.__dict__ if not status.startswith("_")}

TASKS = {}

class Task(object):
    def __init__(self, url, user, path=None):
        """
        
        :param url: url to Download
        :param user: authentiacated user
        :param path: destination path to store the resulting file
        """
        self.url = url
        self.user = user
        self.task_id = str(uuid.uuid4())
        self.full_path = self._generate_full_path(path)
        self.created = time.time()
        self.status = (self.created, TASK_STATUSES.CREATED)
        Stats.update(None, TASK_STATUSES.CREATED)
        TASKS[self.task_id] = self

    def _generate_full_path(self, path):

        """
        Given the target path generates full_path for 
        the resulting file.
        :param path: target path
        :return: full_path
        """
        full_path = path

        file_name = self._generate_file_name_from_url(self.url)
        return os.path.join(full_path, file_name)

    def _generate_file_name_from_url(self, url):
        """
        If ENABLE_UNIQUE_NAMES is True it will allways geneare
        uniqueu filename. If False it will generate the same name from 
        the same origin. The old file would be override. 
        Examples of unique file_names:
            http://google.com/ --> Unknown-3p4hp34
            http://googlr.com/index.html --> index-ads8a2w.html
        
        :param url: url
        :return: file_name
        """
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
        """
        This updates tasks status and rearranges the Stats.tasks_by_statuses
        counters 
        :param status: 
        """
        Stats.update(self.status[1], status)
        self.status = (round(time.time() - self.created, 4), status)
        log.debug("%(task_id)s %(status)s %(duration)f %(url)s" % dict(
            task_id=self.task_id,
            duration=self.status[0],
            status=self.status[1],
            url=self.url))

    def __repr__(self):
        """
        Nice task representation. 
        :return: json string
        """
        return json.dumps({"id": self.task_id,
                           "url": self.url,
                           "dest": self.full_path,
                           "status": self.status[1],
                           "duration": self.status[0]
                           })
