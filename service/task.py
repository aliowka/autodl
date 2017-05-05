import uuid


class Task(object):
    def __init__(self, url):
        self.url = url
        self.task_id = str(uuid.uuid4())
