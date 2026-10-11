import re

from django.conf import settings
from django.core.signals import request_started
from django.http.cookie import SimpleCookie
from django.utils import timezone
from django.utils.module_loading import import_string

from easyaudit.request_auth import (
    adapters_configured,
    get_request_user,
    get_session_user,
)
from easyaudit.settings import (
    LOGGING_BACKEND,
    REGISTERED_URLS,
    REMOTE_ADDR_HEADER,
    UNREGISTERED_URLS,
    WATCH_REQUEST_EVENTS,
)

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


def get_request_details(environ=None, scope=None):
    """Return the request details to log, and the request's raw cookie header."""
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

    details = {
        "url": path,
        "method": method,
        "query_string": query_string,
        "remote_ip": remote_ip,
    }
    return details, cookie_string


def request_started_handler(sender, **kwargs):
    # With auth adapters configured, EasyAuditMiddleware logs the request after the
    # response instead, once the view has authenticated it.
    if adapters_configured():
        return

    details, cookie_string = get_request_details(
        environ=kwargs.get("environ"), scope=kwargs.get("scope")
    )
    if not should_log_url(details["url"]):
        return

    user = None
    # get the user from cookies
    if cookie_string:
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        session_cookie_name = settings.SESSION_COOKIE_NAME
        if session_cookie_name in cookie:
            user = get_session_user(cookie[session_cookie_name].value)

    # may want to wrap this in an atomic transaction later
    audit_logger.request(
        {
            **details,
            "user_id": getattr(user, "id", None),
            "datetime": timezone.now(),
        }
    )


def log_request_after_response(request):
    """Log a request from the middleware, attributing it through the auth adapters."""
    environ = getattr(request, "environ", None)
    scope = getattr(request, "scope", None)
    if not environ and not scope:
        return

    details, _ = get_request_details(environ=environ, scope=scope)
    if not should_log_url(details["url"]):
        return

    user = get_request_user(request)
    audit_logger.request(
        {
            **details,
            "user_id": getattr(user, "id", None),
            "datetime": timezone.now(),
        }
    )


if WATCH_REQUEST_EVENTS:
    request_started.connect(
        request_started_handler, dispatch_uid="easy_audit_signals_request_started"
    )
