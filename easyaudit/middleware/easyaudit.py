# makes easy-audit thread-safe
import contextlib
from threading import local


class MockRequest:
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.user = user
        super().__init__(*args, **kwargs)


_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_current_user():
    request = get_current_request()
    if request:
        return getattr(request, "user", None)
    return None


def set_current_user(user):
    try:
        _thread_locals.request.user = user
    except AttributeError:
        request = MockRequest(user=user)
        _thread_locals.request = request


def clear_request():
    with contextlib.suppress(AttributeError):
        del _thread_locals.request


class EasyAuditMiddleware:
    """Makes request available to this app signals."""

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = (
            request  # seems redundant w/process_request, but keeping in for now.
        )
        if hasattr(self, "process_request"):
            response = self.process_request(request)
        response = response or self.get_response(request)
        if hasattr(self, "process_response"):
            response = self.process_response(request, response)
        return response

    def process_request(self, request):
        _thread_locals.request = request

    def process_response(self, request, response):
        with contextlib.suppress(AttributeError):
            del _thread_locals.request
        return response

    def process_exception(self, request, exception):
        with contextlib.suppress(AttributeError):
            del _thread_locals.request
