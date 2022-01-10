from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class CRUDEvent(models.Model):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    M2M_CHANGE = 4
    M2M_CHANGE_REV = 5
    M2M_ADD = 6
    M2M_ADD_REV = 7
    M2M_REMOVE = 8
    M2M_REMOVE_REV = 9
    M2M_CLEAR = 10
    M2M_CLEAR_REV = 11

    TYPES = (
        (CREATE, _('Create')),
        (UPDATE, _('Update')),
        (DELETE, _('Delete')),
        (M2M_CHANGE, _('Many-to-Many Change')),
        (M2M_CHANGE_REV, _('Reverse Many-to-Many Change')),
        (M2M_ADD, _('Many-to-Many Add')),
        (M2M_ADD_REV, _('Reverse Many-to-Many Add')),
        (M2M_REMOVE, _('Many-to-Many Remove')),
        (M2M_REMOVE_REV, _('Reverse Many-to-Many Remove')),
        (M2M_CLEAR, _('Many-to-Many Clear')),
        (M2M_CLEAR_REV, _('Reverse Many-to-Many Clear')),
    )

    event_type = models.SmallIntegerField(choices=TYPES, verbose_name=_('Event type'))
    object_id = models.CharField(max_length=255, verbose_name=_('Object ID'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, db_constraint=False, verbose_name=_('Content type'))
    object_repr = models.TextField(null=True, blank=True, verbose_name=_('Object representation'))
    object_json_repr = models.TextField(null=True, blank=True, verbose_name=_('Object JSON representation'))
    changed_fields = models.TextField(null=True, blank=True, verbose_name=_('Changed fields'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             blank=True, on_delete=models.SET_NULL,
                             db_constraint=False, verbose_name=_('User'))
    user_pk_as_string = models.CharField(max_length=255, null=True, blank=True,
                                         help_text=_('String version of the user pk'), verbose_name=_('User PK as string'))
    datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('Date time'))

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
    login_type = models.SmallIntegerField(choices=TYPES, verbose_name=_('Event type'))
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Username'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, db_constraint=False,
                             verbose_name=_('User'))
    remote_ip = models.CharField(max_length=50, null=True, db_index=True, verbose_name=_('Remote IP'))
    datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('Date time'))

    class Meta:
        verbose_name = _('login event')
        verbose_name_plural = _('login events')
        ordering = ['-datetime']


class RequestEvent(models.Model):
    url = models.CharField(null=False, db_index=True, max_length=254, verbose_name=_('URL'))
    method = models.CharField(max_length=20, null=False, db_index=True, verbose_name=_('Method'))
    query_string = models.TextField(null=True, verbose_name=_('Query string'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, db_constraint=False,
                             verbose_name=_('User'))
    remote_ip = models.CharField(max_length=50, null=True, db_index=True, verbose_name=_('Remote IP'))
    datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('Date time'))

    class Meta:
        verbose_name = _('request event')
        verbose_name_plural = _('request events')
        ordering = ['-datetime']
