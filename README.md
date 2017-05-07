# AUTODL Overview and Installation

Installing Using Virtualenv

1. Create virtualenv:
`virtualenv -p /usr/bin/python2.7 my_project`
2. Activate virtualenv:
`source /my_project/bin/activate`
3. There is a requirements.txt which I created with freezing my
freshly created virtualenv.
It looks like there is many unnecessary libraries. Indeed in the project I'm
 usgin only `Twisted` for async io (service), `requests` for blocking io (client),
 `Click` for args parsing and `expiredict` for a simple dictionary with ttl.
 Those are the minimal list of requirements.
 Nevertheless I think it would be more convenient to just:
`pip install -r autodl/requirements.txt`

#### Running autdl-service
Activate the virtualenve and then:
`./service/autodl_service.py` or
`../service/autodl_service.py 100` sets the max_tasks_num to 100

#### Running autdl client
Activate the virtualenve and then:
`./client/autodl.py --help`
to see implemented command. If you want to get more info regarding specific
command use --help with conjunction with the command for example:
`./client/autodl.py status --help`

## Design Overview
The project consists of two major parts: service and client.

#### Service
Service and all it's backend stuff is proudly served by Twisted.

Service receives HTTP requests and rout them to specified Resourses.
There is a separate handler for each type of requests:
Add, Stats, Resume, Pause, etc.

There is WorkersManager and Workers

There is a shared Queue which provides convenient communication
between Service and WorkerManager.

There is a Task object. And their is TASKS key-value store which used
for queries tasks information by task_id.

Each time Service receives ADD request, it creates a new task and
places it in Queue.

WorkerManager runs multiply runners (LoopingCalls). Their number equal
to max_tasks_num. Those runners poles the Queue. While empty the runners
are slowed down with IDLE_DELAY. When there is a task in queue, eventualy
one of the runners will pick it up and Create the Worker for this specific
task.

Worker responsibility is to download the corresponding task's URL
and save it's content to disk, to the specified folder. All thetime
the Worker is busy with the task, it's runner is "waiting" for him.
Once Worker is done it exits and the runner is notified to proceed.

There is Stats and DownloadStats classes, which holds the statistics.
Stats is for the tasks statuses and counters. DownloadStats is for
download statuses counters. The last is currently implemented with
lazy expiring dictionary. The TTL is set to 10 minutes.

#### Client
Client is fairly straightforward. It uses requests library for communication with
the service, and Click library for command line arguments support.
Each request it issue is Authenticated with BasicAuth. The username:password
encoded to base64 and appended to the Authentiaction header. Currently
there is no any meaning for the password portion of the credentials.
Usename must be valid username of existing user on the remote machine,
which service is running on. Otherwise Unautherized exception is returned
by the Service.

### Integration Test
The test accomplished by actually running the service and the client in
in a separate subprocess, and inspecting the client output.
There is a couple of test cases for adding tasks, pauseing, resuming workers,
clearing enqued tasks and getting stats.



