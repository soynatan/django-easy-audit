from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

try: # Django 2.0
    from django.urls import reverse
except: # Django < 2.0
    from django.core.urlresolvers import reverse

from django.utils.safestring import mark_safe
from django.utils.html import escape
from . import settings
from .models import CRUDEvent, LoginEvent, RequestEvent
from .admin_helpers import prettify_json, EasyAuditModelAdmin
from .settings import (CRUD_EVENT_LIST_FILTER, LOGIN_EVENT_LIST_FILTER, REQUEST_EVENT_LIST_FILTER,
                       CRUD_EVENT_SEARCH_FIELDS, LOGIN_EVENT_SEARCH_FIELDS, REQUEST_EVENT_SEARCH_FIELDS,
                       READONLY_EVENTS)

# CRUD events
class CRUDEventAdmin(EasyAuditModelAdmin):
    list_display = ['get_event_type_display', 'get_content_type', 'object_id', 'object_repr_link', 'user_link', 'datetime']
    date_hierarchy = 'datetime'
    list_filter = CRUD_EVENT_LIST_FILTER
    search_fields = CRUD_EVENT_SEARCH_FIELDS
    readonly_fields = ['event_type', 'object_id', 'get_content_type',
                       'object_repr', 'object_json_repr_prettified', 'get_user',
                       'user_pk_as_string', 'datetime', 'changed_fields_prettified']
    exclude = ['object_json_repr', 'changed_fields']

    def get_changelist_instance(self, *args, **kwargs):
        changelist_instance = super().get_changelist_instance(*args, **kwargs)
        content_type_ids = [obj.content_type_id for obj in changelist_instance.result_list]
        self.content_types_by_id = {content_type.id: content_type for content_type in ContentType.objects.filter(id__in=content_type_ids)}
        return changelist_instance

    def get_content_type(self, obj):
        return self.content_types_by_id[obj.content_type_id]

    get_content_type.short_description = "Content Type"

    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    get_user.short_description = "User"

    def object_repr_link(self, obj):
        if obj.event_type == CRUDEvent.DELETE:
            html = obj.object_repr
        else:
            escaped_obj_repr = escape(obj.object_repr)
            try:
                content_type = self.get_content_type(obj)
                url = reverse("admin:%s_%s_change" % (
                    content_type.app_label,
                    content_type.model,
                ), args=(obj.object_id,))
                html = '<a href="%s">%s</a>' % (url, escaped_obj_repr)
            except Exception:
                html = escaped_obj_repr
        return mark_safe(html)

    object_repr_link.short_description = 'object repr'

    def object_json_repr_prettified(self, obj):
        return prettify_json(obj.object_json_repr)

    object_json_repr_prettified.short_description = 'object json repr'

    def changed_fields_prettified(self, obj):
        return prettify_json(obj.changed_fields)

    changed_fields_prettified.short_description = 'changed fields'


if settings.ADMIN_SHOW_MODEL_EVENTS:
    admin.site.register(CRUDEvent, CRUDEventAdmin)


# Login events
class LoginEventAdmin(EasyAuditModelAdmin):
    list_display = ['datetime', 'get_login_type_display', 'user_link', "get_username", 'remote_ip']
    date_hierarchy = 'datetime'
    list_filter = LOGIN_EVENT_LIST_FILTER
    search_fields = LOGIN_EVENT_SEARCH_FIELDS
    readonly_fields = ['login_type', 'get_username', 'get_user', 'remote_ip', 'datetime', ]

    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    get_user.short_description = "User"

    def get_username(self, obj):
        user = self.get_user(obj)
        username = user.get_username() if user else None
        return username

    get_username.short_description = "User name"


if settings.ADMIN_SHOW_AUTH_EVENTS:
    admin.site.register(LoginEvent, LoginEventAdmin)


# Request events
class RequestEventAdmin(EasyAuditModelAdmin):
    list_display = ['datetime', 'user_link', 'method', 'url', 'remote_ip']
    date_hierarchy = 'datetime'
    list_filter = REQUEST_EVENT_LIST_FILTER
    search_fields = REQUEST_EVENT_SEARCH_FIELDS
    readonly_fields = ['url', 'method', 'query_string', 'get_user', 'remote_ip', 'datetime', ]

    def get_user(self, obj):
        return self.users_by_id.get(obj.user_id)

    get_user.short_description = "User"


if settings.ADMIN_SHOW_REQUEST_EVENTS:
    admin.site.register(RequestEvent, RequestEventAdmin)
