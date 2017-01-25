from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


# Create your models here.
class CRUDEvent(models.Model):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    TYPES = (
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
    )

    event_type = models.SmallIntegerField(choices=TYPES)
    object_id = models.IntegerField()  # we should try to allow other ID types
    content_type = models.ForeignKey(ContentType)
    object_repr = models.CharField(max_length=255, null=True, blank=True)
    object_json_repr = models.TextField(null=True, blank=True)
    # let the PK for the user remain, but do not assume the user still exists in the database
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True)

    def is_create(self):
        return self.CREATE == self.event_type

    def is_update(self):
        return self.UPDATE == self.event_type

    def is_delete(self):
        return self.DELETE == self.event_type

    class Meta:
        verbose_name = 'CRUD event'
        verbose_name_plural = 'CRUD events'
        ordering = ['-datetime']


class LoginEvent(models.Model):
    LOGIN = 0
    LOGOUT = 1
    FAILED = 2
    TYPES = (
        (LOGIN, 'Login'),
        (LOGOUT, 'Logout'),
        (FAILED, 'Failed login'),
    )
    login_type = models.SmallIntegerField(choices=TYPES)
    username = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'login event'
        verbose_name_plural = 'login events'
        ordering = ['-datetime']
