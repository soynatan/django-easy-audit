try:
    from django.utils.deprecation import MiddlewareMixin
except:
    # not required in <= 1.9
    MiddlewareMixin = object

class EasyAuditMiddleware(MiddlewareMixin):
    """Makes request available to this app signals."""

    request = None

    def process_request(self, request):
        EasyAuditMiddleware.request = request
