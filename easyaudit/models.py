from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

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
    object_id = models.IntegerField()
    content_type = models.ForeignKey(ContentType)
    object_repr = models.CharField(max_length=255, null=True, blank=True)
    object_json_repr = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    datetime = models.DateTimeField(auto_now_add=True)

    def is_create(self):
        return self.CREACION == self.tipo

    def is_update(self):
        return self.MODIFICACION == self.tipo
    
    def is_delete(self):
        return self.ELIMINACION == self.tipo

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
        (FAILED, 'Login fallido'),
    )
    login_type = models.SmallIntegerField(choices=TYPES)
    username = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'login event'
        verbose_name_plural = 'login events'
        ordering = ['-datetime']
