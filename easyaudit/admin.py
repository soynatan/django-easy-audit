from django.contrib import admin
from . import models


# CRUD events
class CRUDEventAdmin(admin.ModelAdmin):
    list_display = ['get_event_type_display', 'content_type', 'object_id', 'object_repr', 'user', 'datetime']


admin.site.register(models.CRUDEvent, CRUDEventAdmin)


# Login events
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'get_login_type_display', 'username', 'user']


admin.site.register(models.LoginEvent, LoginEventAdmin)


# Request events
class RequestEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'method', 'user', 'uri']


admin.site.register(models.RequestEvent, RequestEventAdmin)