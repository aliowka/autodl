#!/usr/bin/python
import os
import requests
import getpass
import urlparse
from requests.auth import HTTPBasicAuth

import click
from service.settings import PORT

@click.group()
def cli():
    pass

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
@click.argument('url')
@click.argument('path', default=None, required=False)
def add(host, port, url, path):
    """Enqueue URL to Auotodownloaders queue"""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    path = path or os.path.join(os.path.expanduser("~%s" % user), "autodl-storage")
    print "Connecting to http://%s:%s" % (host, port)
    print "Sending:", url
    print "Authenticating as:", user
    print "Download destination:", path
    resp = requests.post(urlparse.urljoin(service_url, "add"),
                         auth=HTTPBasicAuth(user, "password"),
                         data={"url": url, "path": path})
    print "Response:", resp.status_code, resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
@click.argument('task_id')
def task(host, port, task_id):
    """Clear all enqueued URLs"""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    print "Getting status for task:", task_id
    print "Connecting to http://%s:%s" % (host, port)
    print "Authenticating as:", user
    service_url = urlparse.urljoin(service_url, "task?task_id=%s" % task_id)
    print service_url
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print "Response:", resp.status_code, resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
def clear(host, port):
    """Clear all enqueued URLs"""
    print host, port

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
def pause(host, port):
    """Don't start new downloads of enqeuued URLs"""
    print host, port

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
def resume(host, port):
    """Allow new downloads of enqueued URLs"""
    print host, port

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=PORT)
def stats(host, port):
    """Show stats"""
    print host, port, url


if __name__ == '__main__':
    cli()
