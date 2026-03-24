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
REGISTERED_URL_PATTERNS = [re.compile(url) for url in REGISTERED_URLS]
UNREGISTERED_URL_PATTERNS = [re.compile(url) for url in UNREGISTERED_URLS]


def should_log_url(url):
    # check if current url is blacklisted
    for pattern in UNREGISTERED_URL_PATTERNS:
        if pattern.match(url):
            return False

    # only audit URLs listed in REGISTERED_URLS (if it's set)
    if REGISTERED_URL_PATTERNS:
        return any(pattern.match(url) for pattern in REGISTERED_URL_PATTERNS)

    # all good
    return True


def _get_remote_addr_header():
    return getattr(settings, "DJANGO_EASY_AUDIT_REMOTE_ADDR_HEADER", REMOTE_ADDR_HEADER)


def _get_asgi_headers(scope):
    return {
        key.decode("latin1").lower(): value.decode("latin1")
        for key, value in scope.get("headers", [])
    }


def _get_asgi_remote_ip(scope, headers):
    remote_addr_header = _get_remote_addr_header()
    if remote_addr_header != "REMOTE_ADDR":
        asgi_header_name = (
            remote_addr_header.removeprefix("HTTP_").lower().replace("_", "-")
        )
        remote_ip = headers.get(asgi_header_name)
        if remote_ip:
            return remote_ip

    return next(iter(scope.get("client", ("0.0.0.0", 0))))  # noqa: S104


def _get_request_details(environ, scope):
    if environ:
        return {
            "cookie_string": environ.get("HTTP_COOKIE"),
            "method": environ["REQUEST_METHOD"],
            "path": environ["PATH_INFO"],
            "query_string": environ["QUERY_STRING"],
            "remote_ip": environ.get(_get_remote_addr_header()),
        }

    headers = _get_asgi_headers(scope)
    return {
        "cookie_string": headers.get("cookie"),
        "method": scope.get("method"),
        "path": scope.get("path"),
        "query_string": scope.get("query_string"),
        "remote_ip": _get_asgi_remote_ip(scope, headers),
    }


def _get_user_from_cookie(cookie_string):
    user = None
    if cookie_string:
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

    return user


def request_started_handler(sender, **kwargs):
    request_details = _get_request_details(
        kwargs.get("environ"),
        kwargs.get("scope") or {},
    )
    path = request_details["path"]
    if not should_log_url(path):
        return

    user = _get_user_from_cookie(request_details["cookie_string"])

    # may want to wrap this in an atomic transaction later
    audit_logger.request(
        {
            "url": path,
            "method": request_details["method"],
            "query_string": request_details["query_string"],
            "user_id": getattr(user, "id", None),
            "remote_ip": request_details["remote_ip"],
            "datetime": timezone.now(),
        }
    )


if WATCH_REQUEST_EVENTS:
    request_started.connect(
        request_started_handler, dispatch_uid="easy_audit_signals_request_started"
    )
