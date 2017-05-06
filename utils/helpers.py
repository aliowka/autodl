from defer import Deferred

import time
from twisted.web.http import _escape


def waiting_deferred(reactor, delay_sec):
    d = Deferred()
    reactor.callLater(delay_sec, d.callback, True)
    return d


def timedLogFormatter(timestamp, request):
    """
    A custom request formatter.  This is whats used when each request line is formatted.

    :param timestamp: 
    :param request: A twisted.web.server.Request instance
    """
    agent = _escape(request.getHeader(b"user-agent") or b"-")
    duration = round(time.time() - request.started, 4)
    line = (
        u'%(duration)ss "%(ip)s" "%(method)s %(uri)s %(protocol)s %(args)s" '
        u'%(code)d %(length)s"' % dict(
            ip=_escape(request.getClientIP() or b"-"),
            duration=duration,
            method=_escape(request.method),
            uri=_escape(request.uri),
            args=_escape(str(request.args)),
            protocol=_escape(request.clientproto),
            code=request.code,
            length=request.sentLength or u"-",
        ))
    return line