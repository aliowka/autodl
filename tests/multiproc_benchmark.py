# -*- coding: utf-8 -*-
import getpass
import os
import time
import requests
from multiprocessing import Pool
from service.task import Task


def _save_content_to_file(content, task):
    path = task.full_path
    path_dir = os.path.dirname(path)
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)

    with open(path, "w+") as f:
        f.write(content.encode("utf-8"))

    return path


def f(url):
    task = Task(url, getpass.getuser(), "/tmp/autodl-test-multiproc")
    content = requests.get(url).text
    return _save_content_to_file(content, task)


if __name__ == '__main__':
    bulk_size = 30
    p = Pool(bulk_size)
    st = time.time()
    print p.map(f, ["http://autodesk.com"] * bulk_size)
    print "multiprocessing.Pool: %s tasks/sec" % (bulk_size / (time.time() - st))
