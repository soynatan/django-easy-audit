from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class CRUDEvent(models.Model):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    M2M_CHANGE = 4
    M2M_CHANGE_REV = 5

    TYPES = (
        (CREATE, _('Create')),
        (UPDATE, _('Update')),
        (DELETE, _('Delete')),
        (M2M_CHANGE, _('Many-to-Many Change')),
        (M2M_CHANGE_REV, _('Reverse Many-to-Many Change')),
    )

    event_type = models.SmallIntegerField(choices=TYPES)
    object_id = models.IntegerField()  # we should try to allow other ID types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_repr = models.TextField(null=True, blank=True)
    object_json_repr = models.TextField(null=True, blank=True)
    changed_fields = models.TextField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             blank=True, on_delete=models.SET_NULL)
    user_pk_as_string = models.CharField(max_length=255, null=True, blank=True,
                                     help_text=_('String version of the user pk'))
    datetime = models.DateTimeField(auto_now_add=True)

    def is_create(self):
        return self.CREATE == self.event_type

    def is_update(self):
        return self.UPDATE == self.event_type

    def is_delete(self):
        return self.DELETE == self.event_type

    class Meta:
        verbose_name = _('CRUD event')
        verbose_name_plural = _('CRUD events')
        ordering = ['-datetime']
        index_together = ['object_id', 'content_type', ]


class LoginEvent(models.Model):
    LOGIN = 0
    LOGOUT = 1
    FAILED = 2
    TYPES = (
        (LOGIN, _('Login')),
        (LOGOUT, _('Logout')),
        (FAILED, _('Failed login')),
    )
    login_type = models.SmallIntegerField(choices=TYPES)
    username = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL)
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('login event')
        verbose_name_plural = _('login events')
        ordering = ['-datetime']


class RequestEvent(models.Model):
    url = models.TextField(null=False, db_index=True)
    method = models.CharField(max_length=20, null=False, db_index=True)
    query_string = models.TextField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL)
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('request event')
        verbose_name_plural = _('request events')
        ordering = ['-datetime']
