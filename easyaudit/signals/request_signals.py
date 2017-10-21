from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.signals import request_started
from django.utils import six, timezone

from easyaudit.models import RequestEvent
from easyaudit.settings import UNREGISTERED_URLS, WATCH_REQUEST_EVENTS

import re


def should_log_url(url):
    # check if current url is blacklisted
    for unregistered_url in UNREGISTERED_URLS:
        pattern = re.compile(unregistered_url)
        if pattern.match(url):
            return False
    return True


def request_started_handler(sender, environ, **kwargs):
    if not should_log_url(environ['PATH_INFO']):
        return

    # get the user from cookies
    user = None
    if 'HTTP_COOKIE' in environ:
        cookie = six.moves.http_cookies.SimpleCookie() # python3 compatibility
        cookie.load(environ['HTTP_COOKIE'])

        if 'sessionid' in cookie:
            session_id = cookie['sessionid'].value

            try:
                session = Session.objects.get(session_key=session_id)
            except Session.DoesNotExist:
                session = None

            if session:
                user_id = session.get_decoded()['_auth_user_id']
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    user = None

    request_event = RequestEvent.objects.create(
        url=environ['PATH_INFO'],
        method=environ['REQUEST_METHOD'],
        query_string=environ['QUERY_STRING'],
        user=user,
        remote_ip=environ['REMOTE_ADDR'],
        datetime=timezone.now()
    )


if WATCH_REQUEST_EVENTS:
    request_started.connect(request_started_handler, dispatch_uid='easy_audit_signals_request_started')