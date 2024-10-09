# makes easy-audit thread-safe
import contextlib
from typing import Callable

from asgiref.local import Local
from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http.request import HttpRequest
from django.http.response import HttpResponse


class MockRequest:
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.user = user
        super().__init__(*args, **kwargs)


_thread_locals = Local()


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
    async_capable = True
    sync_capable = True

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if iscoroutinefunction(self):
            return self.__acall__(request)

        _thread_locals.request = request
        response = self.get_response(request)

        with contextlib.suppress(AttributeError):
            del _thread_locals.request

        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        _thread_locals.request = request

        response = await self.get_response(request)

        with contextlib.suppress(AttributeError):
            del _thread_locals.request

        return response
