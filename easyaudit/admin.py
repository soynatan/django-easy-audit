from django.contrib import admin
from . import models

# Register your models here.
class CRUDEventAdmin(admin.ModelAdmin):
    list_display = ['get_event_type_display', 'content_type', 'object_id', 'object_repr', 'user', 'datetime']

admin.site.register(models.CRUDEvent, CRUDEventAdmin)

class LoginEventAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'get_login_type_display', 'username', 'user']

admin.site.register(models.LoginEvent, LoginEventAdmin)
