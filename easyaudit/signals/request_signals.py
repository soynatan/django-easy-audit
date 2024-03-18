import re
from importlib import import_module

from django.conf import settings
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.signals import request_started
from django.http.cookie import SimpleCookie
from django.utils import timezone
from django.utils.module_loading import import_string

from easyaudit.settings import (
    LOGGING_BACKEND,
    REGISTERED_URLS,
    REMOTE_ADDR_HEADER,
    UNREGISTERED_URLS,
    WATCH_REQUEST_EVENTS,
)

session_engine = import_module(settings.SESSION_ENGINE)
audit_logger = import_string(LOGGING_BACKEND)()


def should_log_url(url):
    # check if current url is blacklisted
    for unregistered_url in UNREGISTERED_URLS:
        pattern = re.compile(unregistered_url)
        if pattern.match(url):
            return False

    # only audit URLs listed in REGISTERED_URLS (if it's set)
    if len(REGISTERED_URLS) > 0:
        for registered_url in REGISTERED_URLS:
            pattern = re.compile(registered_url)
            if pattern.match(url):
                return True
        return False

    # all good
    return True


def request_started_handler(sender, **kwargs):
    environ = kwargs.get("environ")
    scope = kwargs.get("scope")
    if environ:
        path = environ["PATH_INFO"]
        cookie_string = environ.get("HTTP_COOKIE")
        remote_ip = environ.get(REMOTE_ADDR_HEADER, None)
        method = environ["REQUEST_METHOD"]
        query_string = environ["QUERY_STRING"]

    else:
        method = scope.get("method")
        path = scope.get("path")
        headers = dict(scope.get("headers"))
        cookie_string = headers.get(b"cookie")
        if isinstance(cookie_string, bytes):
            cookie_string = cookie_string.decode("utf-8")
        remote_ip = next(iter(scope.get("client", ("0.0.0.0", 0))))  # noqa: S104
        query_string = scope.get("query_string")

    if not should_log_url(path):
        return

    user = None
    # get the user from cookies
    if not user and cookie_string:
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        session_cookie_name = settings.SESSION_COOKIE_NAME
        if session_cookie_name in cookie:
            session_id = cookie[session_cookie_name].value

            try:
                session = session_engine.SessionStore(session_key=session_id).load()
            except Session.DoesNotExist:
                session = None

            if session and AUTH_SESSION_KEY in session:
                user_id = session.get(AUTH_SESSION_KEY)
                try:
                    user = get_user_model().objects.get(id=user_id)
                except Exception:
                    user = None

    # may want to wrap this in an atomic transaction later
    audit_logger.request(
        {
            "url": path,
            "method": method,
            "query_string": query_string,
            "user_id": getattr(user, "id", None),
            "remote_ip": remote_ip,
            "datetime": timezone.now(),
        }
    )


if WATCH_REQUEST_EVENTS:
    request_started.connect(
        request_started_handler, dispatch_uid="easy_audit_signals_request_started"
    )
