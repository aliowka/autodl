import json
import os
import unittest

import subprocess

import re

import time

from service import autodl_service
from service.settings import ROOT_DIR
import multiprocessing

from service.task import TASK_STATUSES


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.host = "localhost"
        autodl_service.SERVICE_PORT = 9999
        self.service = multiprocessing.Process(target=autodl_service.main)
        self.service.start()
        time.sleep(1)

    def tearDown(self):
        self.service.terminate()

    def test_add(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "add", "--port", str(autodl_service.SERVICE_PORT),
                        "http://google.com", "/tmp/test"])

        response = self._run_command(cmd)
        task = json.loads(response["task"])

        self.assertEqual(TASK_STATUSES.ENQUEUED, task["status"])
        self.assertTrue(os.path.exists(task["dest"]))
        self.assertGreater(len(open(task["dest"]).read()), 0)

    def test_pause(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "pause", "--port", str(autodl_service.SERVICE_PORT)])

        response = self._run_command(cmd)

        self.assertEqual(response["message"], "Pausing Workers")

    def test_resume(self):
        cmd = " ".join([os.path.join(ROOT_DIR, "client", "autodl.py"),
                        "resume", "--port", str(autodl_service.SERVICE_PORT)])

        response = self._run_command(cmd)
        self.assertEqual(response["message"], "Resuming Workers")

    def _run_command(self, cmd):
        self.client_action = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
        )
        output = self.client_action.communicate()[0]
        time.sleep(1)
        response = json.loads(output.strip())
        return response

if __name__ == '__main__':
    unittest.main()
