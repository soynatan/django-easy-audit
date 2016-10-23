class DjangoEasyAuditMiddleware(object):
    """Makes request available to this app signals."""

    request = None

    def process_request(self, request):
        DjangoEasyAuditMiddleware.request = request
