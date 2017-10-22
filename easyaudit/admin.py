from django.contrib import admin
from . import models, settings

# CRUD events
class CRUDEventAdmin(admin.ModelAdmin):
    list_display = ['get_event_type_display', 'content_type', 'object_id', 'object_repr', 'user', 'datetime']


if settings.ADMIN_SHOW_MODEL_EVENTS:
    admin.site.register(models.CRUDEvent, CRUDEventAdmin)


# Login events
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'get_login_type_display', 'user', 'username', 'remote_ip']


if settings.ADMIN_SHOW_AUTH_EVENTS:
    admin.site.register(models.LoginEvent, LoginEventAdmin)


# Request events
class RequestEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'user', 'method', 'url', 'remote_ip']


if settings.ADMIN_SHOW_REQUEST_EVENTS:
    admin.site.register(models.RequestEvent, RequestEventAdmin)