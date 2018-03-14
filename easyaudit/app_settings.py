from django.conf import settings

CRUD_EVENT_LIST_FILTER = getattr(settings, 'EASY_AUDIT_CRUD_EVENT_LIST_FILTER', ['event_type', 'content_type', 'user', 'datetime', ])
LOGIN_EVENT_LIST_FILTER = getattr(settings, 'EASY_AUDIT_LOGIN_EVENT_LIST_FILTER', ['login_type', 'user', 'datetime', ])
REQUEST_EVENT_LIST_FILTER = getattr(settings, 'EASY_AUDIT_REQUEST_EVENT_LIST_FILTER', ['method', 'user', 'datetime', ])

