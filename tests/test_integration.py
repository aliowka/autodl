import json
import os
import unittest
import subprocess
import time
from service import autodl_service
from service.settings import ROOT_DIR
import multiprocessing
from service.task import TASK_STATUSES


class MyTestCase(unittest.TestCase):
    def setUp(self):
        """
        Override service port to not collide with "production" version
        Run "autodl-service" in a separate process 
        Test cases use real client "autodl" as a subprocess to interact with the 
        service.
        """
        self.host = "localhost"
        autodl_service.SERVICE_PORT = 9999
        self.service = multiprocessing.Process(target=autodl_service.main)
        self.service.start()
        time.sleep(1)

    def tearDown(self):
        # close service
        self.service.terminate()

    def test_pause_resume(self):
        self._pause()

        bulk_size = 3
        self._add_many_tasks(bulk_size, with_file=False)

        # after pausing and adding tasks there should be all of them Enqueued
        # and 0 Downloadin and 0 Finished
        response = self._stats()
        self.assertEqual(0, response["tasks"][TASK_STATUSES.DOWNLOADING])
        self.assertEqual(0, response["tasks"][TASK_STATUSES.FINISHED])
        self.assertEqual(bulk_size, response["tasks"][TASK_STATUSES.ENQUEUED])

        # after resuming, there should be 0 Enqueued and all of them Finished.
        self._resume()
        response = self._stats()
        self.assertEqual(0, response["tasks"][TASK_STATUSES.ENQUEUED])
        self.assertEqual(bulk_size, response["tasks"][TASK_STATUSES.FINISHED])

    def test_clear(self):
        self._pause()

        bulk_size = 3
        self._add_many_tasks(bulk_size, with_file=False)

        # after pausing and adding tasks there should be all of them Enqueued
        # and 0 Downloadin and 0 Finished

        response = self._stats()
        self.assertEqual(0, response["tasks"][TASK_STATUSES.DOWNLOADING])
        self.assertEqual(0, response["tasks"][TASK_STATUSES.FINISHED])
        self.assertEqual(bulk_size, response["tasks"][TASK_STATUSES.ENQUEUED])

        self._clear()

        # After pasing, adding tasks and clearing, there should be all of them in CLEARED status.
        response = self._stats()
        self.assertEqual(0, response["tasks"][TASK_STATUSES.ENQUEUED])
        self.assertEqual(0, response["tasks"][TASK_STATUSES.DOWNLOADING])
        self.assertEqual(0, response["tasks"][TASK_STATUSES.FINISHED])
        self.assertEqual(bulk_size, response["tasks"][TASK_STATUSES.CLEARED])

    def test_set_new_max_tasks(self):
        """
        Testing maximum tasks limit.
        The test consists of pausing the workers,
        adding many tasks and setting the max_task_num to
        something much smaller then the number of tasks added.
        Resume the workers and pole in a loop for DOWNLOADING tasks.
        Since the Downloading is the heaviest part of the process it's 
        prety sure to pole this counter for the number of currently running tasks.
        """

        bulk_size = 10
        max_tasks = 2
        self._pause()
        self._add_many_tasks(bulk_size, with_file=False)
        self._set_new_max_tasks(max_tasks)
        self._resume()

        while True:
            response = self._stats()
            self.assertGreaterEqual(max_tasks, response["tasks"][TASK_STATUSES.DOWNLOADING])
            if bulk_size == response["tasks"][TASK_STATUSES.FINISHED]:
                break

    def _add_many_tasks(self, bulk_size, with_file=True):
        for _ in xrange(bulk_size):
            self._add(with_file)

    def _add(self, with_file=True):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "add", "--port", str(autodl_service.SERVICE_PORT),
                        "http://autodesk.com", "/tmp/test"])
        response = self._run_command(cmd)
        task = json.loads(response["task"])
        time.sleep(1)
        self.assertEqual(TASK_STATUSES.ENQUEUED, task["status"])

        self.assertEqual(with_file, os.path.exists(task["dest"]))
        if with_file:
            self.assertGreater(len(open(task["dest"]).read()), 0)

        return response

    def _set_new_max_tasks(self, max_tasks):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "update_tasks_num", "--port", str(autodl_service.SERVICE_PORT),
                        str(max_tasks)])
        response = self._run_command(cmd)
        self.assertEqual("max_tasks set to %s" % max_tasks, response["message"])
        return response


    def _clear(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "clear", "--port", str(autodl_service.SERVICE_PORT)])
        response = self._run_command(cmd)
        self.assertEqual(response["message"], "Enqueued tasks cleared")
        return response

    def _pause(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "pause", "--port", str(autodl_service.SERVICE_PORT)])
        response = self._run_command(cmd)
        self.assertEqual(response["message"], "Pausing Workers")
        return response

    def _stats(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "stats", "--port", str(autodl_service.SERVICE_PORT)])
        response = self._run_command(cmd)
        return response

    def _resume(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "resume", "--port", str(autodl_service.SERVICE_PORT)])
        response = self._run_command(cmd)
        return response

    def _run_command(self, cmd):
        self.client_action = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
        )
        output = self.client_action.communicate()[0]
        response = json.loads(output.strip())
        return response


if __name__ == '__main__':
    unittest.main()
