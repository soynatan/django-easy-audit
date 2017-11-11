import json
from django.contrib import admin
from django.core import urlresolvers
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from . import models, settings


def get_user_link(user):
    """
    Helper to get admin url for given user
    """
    if user is None:
        return '-'
    try:
        user_model = get_user_model()
        url = urlresolvers.reverse("admin:%s_%s_change" % (
            user_model._meta.app_label,
            user_model._meta.model_name,
        ), args=(user.id,))
        html = '<a href="%s">%s</a>' % (url, str(user))
    except:
        html = str(user)
    return html


# CRUD events
class CRUDEventAdmin(admin.ModelAdmin):
    list_display = ['get_event_type_display', 'content_type', 'object_id', 'object_repr_link', 'user_link', 'datetime']
    date_hierarchy = 'datetime'
    list_filter = ['event_type', 'content_type', 'user', 'datetime', ]
    search_fields = ['=object_id', 'object_json_repr', ]
    readonly_fields = ['event_type', 'object_id', 'content_type', 'object_repr',
        'object_json_repr_prettified', 'object_json_repr', 'user', 'user_pk_as_string', 'datetime', ]

    def object_repr_link(self, obj):
        try:
            url = urlresolvers.reverse("admin:%s_%s_change" % (
                obj.content_type.app_label,
                obj.content_type.model,
            ), args=(obj.object_id,))
            html = '<a href="%s">%s</a>' % (url, obj.object_repr)
        except:
            html = obj.object_repr
        return mark_safe(html)
    object_repr_link.short_description = 'object repr'

    def user_link(self, obj):
        return mark_safe(get_user_link(obj.user))
    user_link.short_description = 'user'

    def object_json_repr_prettified(self, obj):
        try:
            data = json.loads(obj.object_json_repr)
            html = '<pre>' + json.dumps(data, sort_keys=True, indent=4) + '</pre>'
        except:
            html = obj.object_json_repr
        return mark_safe(html)
    object_json_repr_prettified.short_description = 'object json repr'


if settings.ADMIN_SHOW_MODEL_EVENTS:
    admin.site.register(models.CRUDEvent, CRUDEventAdmin)


# Login events
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'get_login_type_display', 'user_link', 'username', 'remote_ip']
    date_hierarchy = 'datetime'
    list_filter = ['login_type', 'user', 'datetime', ]
    search_fields = ['=remote_ip', 'username', ]
    readonly_fields = ['login_type', 'username', 'user', 'remote_ip', 'datetime', ]

    def user_link(self, obj):
        return mark_safe(get_user_link(obj.user))
    user_link.short_description = 'user'


if settings.ADMIN_SHOW_AUTH_EVENTS:
    admin.site.register(models.LoginEvent, LoginEventAdmin)


# Request events
class RequestEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'user_link', 'method', 'url', 'remote_ip']
    date_hierarchy = 'datetime'
    list_filter = ['method', 'user', 'datetime', ]
    search_fields = ['=remote_ip', 'username', 'url', 'query_string', ]
    readonly_fields = ['url', 'method', 'query_string', 'user', 'remote_ip', 'datetime', ]

    def user_link(self, obj):
        return mark_safe(get_user_link(obj.user))
    user_link.short_description = 'user'


if settings.ADMIN_SHOW_REQUEST_EVENTS:
    admin.site.register(models.RequestEvent, RequestEventAdmin)
