try:
    from django.utils.deprecation import MiddlewareMixin
except:
    # no requerido en Django <= 1.9
    MiddlewareMixin = object

class EasyAuditMiddleware(MiddlewareMixin):
    """Makes request available to this app signals."""

    request = None

    def process_request(self, request):
        EasyAuditMiddleware.request = request
