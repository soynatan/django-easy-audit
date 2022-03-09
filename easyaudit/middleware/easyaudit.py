
# makes easy-audit thread-safe
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

class MockRequest(object):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.user = user
        super(MockRequest, self).__init__(*args, **kwargs)


_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    request = get_current_request()
    if request:
        return getattr(request, 'user', None)


def set_current_user(user):
    try:
        _thread_locals.request.user = user
    except AttributeError:
        request = MockRequest(user=user)
        _thread_locals.request = request


def clear_request():
    try:
        del _thread_locals.request
    except AttributeError:
        pass


class EasyAuditMiddleware:

    """Makes request available to this app signals."""
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request  # seems redundant w/process_request, but keeping in for now.
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        response = response or self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response

    def process_request(self, request):
        _thread_locals.request = request
        return None

    def process_response(self, request, response):
        try:
            del _thread_locals.request
        except AttributeError:
            pass
        return response

    def process_exception(self, request, exception):
        try:
            del _thread_locals.request
        except AttributeError:
            pass
        return None
