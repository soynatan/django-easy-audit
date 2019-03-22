from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.signals import request_started
from django.http.cookie import SimpleCookie
from django.utils import six, timezone
from django.conf import settings

from easyaudit.models import RequestEvent
from easyaudit.settings import REMOTE_ADDR_HEADER, UNREGISTERED_URLS, WATCH_REQUEST_EVENTS

import re


def should_log_url(url):
    # check if current url is blacklisted
    for unregistered_url in UNREGISTERED_URLS:
        pattern = re.compile(unregistered_url)
        if pattern.match(url):
            return False
    return True


def request_started_handler(sender, **kwargs):
    scope = kwargs.get('scope')
    headers = dict(scope.get('headers'))
    cookie = headers.get(b'cookie')
    method = scope.get('method')
    path = scope.get('path')
    query_string = scope.get('query_string')
    server = scope.get('server')
    remote_ip = f'{server[0]}:{server[1]}'
    
    if not should_log_url(path):
        return

    # get the user from cookies
    user = None
    if cookie:
        cookie = SimpleCookie() # python3 compatibility
        cookie.load(cookie)

        session_cookie_name = settings.SESSION_COOKIE_NAME
        if session_cookie_name in cookie:
            session_id = cookie[session_cookie_name].value

            try:
                session = Session.objects.get(session_key=session_id)
            except Session.DoesNotExist:
                session = None

            if session:
                user_id = session.get_decoded().get('_auth_user_id')
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    user = None

    print('about to save request')
    RequestEvent.objects.create(
        url=path,
        method=method,
        query_string=query_string,
        user=user,
        remote_ip=remote_ip,
        datetime=timezone.now()
    ).save()


if WATCH_REQUEST_EVENTS:
    request_started.connect(request_started_handler, dispatch_uid='easy_audit_signals_request_started')
