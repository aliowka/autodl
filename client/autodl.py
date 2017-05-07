#!/usr/bin/python
import os
import requests
import getpass
import urlparse
from requests.auth import HTTPBasicAuth

import click
from service.settings import SERVICE_PORT

@click.group()
def cli():
    pass

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
@click.argument('url')
@click.argument('path', default=None, required=False)
def add(host, port, url, path):
    """Enqueue URL to Auotodownloaders queue"""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    path = path or os.path.join(os.path.expanduser("~%s" % user), "autodl-storage")
    resp = requests.post(urlparse.urljoin(service_url, "add"),
                         auth=HTTPBasicAuth(user, "password"),
                         data={"url": url, "path": path})
    print resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
@click.argument('task_id')
def status(host, port, task_id):
    """Get task info"""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    service_url = urlparse.urljoin(service_url, "status?task_id=%s" % task_id)
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
def clear(host, port):
    """Clear all enqueued URLs"""
    service_url = "http://%s:%s/clear" % (host, port)
    user = getpass.getuser()
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
@click.argument('seconds', required=False)
def pause(host, port, seconds):
    """Don't start new downloads of enqeuued URLs"""
    service_url = "http://%s:%s/pause" % (host, port)
    if seconds:
        service_url = "?seconds=".join([service_url, seconds])
    user = getpass.getuser()
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
def resume(host, port):
    """Allow new downloads of enqueued URLs"""
    service_url = "http://%s:%s/resume" % (host, port)
    user = getpass.getuser()
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print resp.text

@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
def stats(host, port):
    """Show statistics for last 10 min."""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    service_url = urlparse.urljoin(service_url, "stats")
    resp = requests.get(service_url, auth=HTTPBasicAuth(user, "password"))
    print resp.text


@cli.command()
@click.option('-h', '--host', default="localhost")
@click.option('-p', '--port', default=SERVICE_PORT)
@click.argument('number', default=10, required=False)
def update_tasks_num(host, port, number):
    """Enqueue URL to Auotodownloaders queue"""
    service_url = "http://%s:%s" % (host, port)
    user = getpass.getuser()
    resp = requests.post(urlparse.urljoin(service_url, "maxtasks"),
                         auth=HTTPBasicAuth(user, "password"),
                         data={"max_tasks_number": number})
    print resp.text


if __name__ == '__main__':
    cli()
