import getpass
import os
from Queue import Queue

import shutil
import time
from twisted.internet import reactor

from service.task import Task
from service.workers_manager_async import WorkersManager


if __name__ == '__main__':

    q = Queue()
    wm = WorkersManager(q)
    path = "/tmp/autodl-test-async"
    if os.path.exists(path):
        shutil.rmtree(path)

    bulk_size = 30
    st = time.time()

    def custom_idle(*args):
        print "Twisted: %s tasks/sec" % (bulk_size / (time.time() - st))
        reactor.stop()

    wm.idle = custom_idle
    for i in xrange(bulk_size):
        task = Task("http://autodesk.com", getpass.getuser(), path)
        q.put(task)

    reactor.callLater(0, wm.resume)
    reactor.run()
