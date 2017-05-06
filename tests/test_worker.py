import os
from pwd import getpwuid

import time
from mock import MagicMock
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from service.task import Task
from service.workers_async import Worker


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.worker = Worker()

    @inlineCallbacks
    def test_process_task(self):
        user = "aliowka"
        expected_content = "Original text here: %s" % time.time()
        self.worker._download_url_content = MagicMock()
        self.worker._download_url_content.return_value = expected_content

        test_task = Task(url="http://dummy.com",
                         user=user,
                         path="/tmp/test")

        file_path = yield self.worker.process_task(test_task)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path) as f:
            self.assertEqual(expected_content, f.read())
        self.assertEqual(user, getpwuid(os.stat(file_path).st_uid).pw_name)
