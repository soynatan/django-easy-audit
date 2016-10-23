class EasyAuditMiddleware(object):
    """Makes request available to this app signals."""

    request = None

    def process_request(self, request):
        EasyAuditMiddleware.request = request
