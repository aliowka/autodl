import getpass
import multiprocessing
import requests
import urlparse

import time
from Queue import Empty
from requests.auth import HTTPBasicAuth

from twisted.trial import unittest

from service.autodl_service import main
from service.settings import PORT
from service.autodl_service import BaseView
from service.task import Task

SERVICE_URL = "http://localhost:%s" % PORT


class MyTestCase(unittest.TestCase):
    def setUp(self):
        BaseView.tasks_queue = multiprocessing.Queue()
        self.service = multiprocessing.Process(target=main)
        self.service.start()
        time.sleep(1)

    def tearDown(self):
        self.service.terminate()

    def _populate_tasks_queue_with_test_data(self, items_number):
        for i in xrange(items_number):
            test_url = "http://dummy-%s.com" % i
            resp = requests.post(urlparse.urljoin(SERVICE_URL, "add"),
                                 auth=HTTPBasicAuth(TEST_USER, ""),
                                 data={"url": test_url})
            self.assertEqual(200, resp.status_code)
            self.assertListEqual(["status", "task"], resp.json().keys())

    def test_add_task_handler(self):
        self._populate_tasks_queue_with_test_data(1)
        task = BaseView.tasks_queue.get()
        self.assertIsInstance(task, Task)

    def test_clear_handler(self):
        items_number = 10
        self._populate_tasks_queue_with_test_data(items_number)

        resp = requests.post(urlparse.urljoin(SERVICE_URL, "clear"),
                             auth=HTTPBasicAuth(getpass.getuser(), ""))
        self.assertEqual(200, resp.status_code)

        with self.assertRaises(Empty):
            BaseView.tasks_queue.get(timeout=1)


if __name__ == '__main__':
    unittest.main()
