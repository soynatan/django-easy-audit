import re
from io import BytesIO

from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.wsgi import WSGIRequest
from django.core.signals import request_started
from django.utils import timezone
from django.utils.module_loading import import_string

from easyaudit.request_auth import adapters_require_response, get_request_user
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
    """Return the request details to log, from a WSGI environ or an ASGI scope."""
    if environ:
        path = environ["PATH_INFO"]
        remote_ip = environ.get(REMOTE_ADDR_HEADER, None)
        method = environ["REQUEST_METHOD"]
        query_string = environ["QUERY_STRING"]

    else:
        method = scope.get("method")
        path = scope.get("path")
        remote_ip = next(iter(scope.get("client", ("0.0.0.0", 0))))  # noqa: S104
        query_string = scope.get("query_string")

    return {
        "url": path,
        "method": method,
        "query_string": query_string,
        "remote_ip": remote_ip,
    }


def log_request(details, request):
    user = get_request_user(request)

    # may want to wrap this in an atomic transaction later
    audit_logger.request(
        {
            **details,
            "user_id": getattr(user, "id", None),
            "datetime": timezone.now(),
        }
    )


def request_started_handler(sender, **kwargs):
    # An adapter that needs the view to have run cannot answer yet, so
    # EasyAuditMiddleware logs the request after the response instead.
    if adapters_require_response():
        return

    environ = kwargs.get("environ")
    scope = kwargs.get("scope")
    details = get_request_details(environ=environ, scope=scope)
    if not should_log_url(details["url"]):
        return

    # The signal carries no request object, so build one for the adapters.
    request = WSGIRequest(environ) if environ else ASGIRequest(scope, BytesIO())
    log_request(details, request)


def log_request_after_response(request):
    """Log a request from the middleware, once the view has authenticated it."""
    environ = getattr(request, "environ", None)
    scope = getattr(request, "scope", None)
    if not environ and not scope:
        return

    details = get_request_details(environ=environ, scope=scope)
    if not should_log_url(details["url"]):
        return

    log_request(details, request)


if WATCH_REQUEST_EVENTS:
    request_started.connect(
        request_started_handler, dispatch_uid="easy_audit_signals_request_started"
    )
