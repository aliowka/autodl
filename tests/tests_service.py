import multiprocessing
import requests
import unittest
import urlparse

import time
from Queue import Empty

from service.autodl_service import main
from service.settings import PORT
from service.autodl_service import BaseView
from service.task import Task

tasks_queue = multiprocessing.Queue()

SERVICE_URL = "http://localhost:%s" % PORT


class MyTestCase(unittest.TestCase):

    def setUp(self):
        BaseView.tasks_queue = tasks_queue
        self.service = multiprocessing.Process(target=main)
        self.service.start()
        time.sleep(1)

    def tearDown(self):
        self.service.terminate()

    def _populate_tasks_queue_with_test_data(self, items_number):
        for i in xrange(items_number):
            test_url = "http://dummy-%s.com" % i
            resp = requests.post(urlparse.urljoin(SERVICE_URL, "add"), data={"url": test_url})
            self.assertEqual(200, resp.status_code)
            self.assertListEqual(["status", "url", "task_id"], resp.json().keys())

    def test_service_is_up(self):
        resp = requests.get("http://localhost:%s/alive" % PORT)
        self.assertEqual(200, resp.status_code)

    def test_add_task_handler(self):
        self._populate_tasks_queue_with_test_data(1)
        task = tasks_queue.get()
        self.assertIsInstance(task, Task)

    def test_clear_handler(self):
        items_number = 100
        self._populate_tasks_queue_with_test_data(items_number)

        resp = requests.post(urlparse.urljoin(SERVICE_URL, "clear"))
        self.assertEqual(200, resp.status_code)

        with self.assertRaises(Empty):
            tasks_queue.get(timeout=1)




if __name__ == '__main__':
    unittest.main()
