# django-easy-audit classes
from .models import CRUDEvent, LoginEvent

# django unregistered classes
from django.db.migrations import Migration
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# user classes
from django.contrib.auth.models import User, AnonymousUser

# signals
from django.db.models import signals as models_signals
from django.contrib.auth import signals as auth_signals

# utils
from django.core import serializers
import datetime

# middleware
from .middleware.easyaudit import EasyAuditMiddleware

# unregistered classes
UNREGISTERED_CLASSES = [CRUDEvent, LoginEvent, Migration, LogEntry, Session, Permission, ContentType]

# signals
def post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-save"""
    try:
        for unregistered_class in UNREGISTERED_CLASSES:
            if isinstance(instance, unregistered_class):
                return False

        object_json_repr = serializers.serialize("json", [instance])

        # creacion o actualizacion?
        if created:
            event_type = CRUDEvent.CREATE
        else:
            event_type = CRUDEvent.UPDATE

        # usuario
        try:
            user = EasyAuditMiddleware.request.user
        except:
            user = None

        if isinstance(user, AnonymousUser):
            user = None

        # crud event
        crud_event = CRUDEvent(
            event_type=event_type,
            object_repr=str(instance),
            object_json_repr=object_json_repr,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            user=user,
            datetime=datetime.datetime.now()
            )

        crud_event.save()
    except:
        pass

def post_delete(sender, instance, using, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-delete"""
    try:
        for unregistered_class in UNREGISTERED_CLASSES:
            if isinstance(instance, unregistered_class):
                return False

        object_json_repr = serializers.serialize("json", [instance])
        
        # user
        user = EasyAuditMiddleware.request.user
        if isinstance(user, AnonymousUser):
            user = None

        # crud event
        crud_event = CRUDEvent(
            event_type=CRUDEvent.DELETE,
            object_repr=str(instance),
            object_json_repr=object_json_repr,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            user=user,
            datetime=datetime.datetime.now()
            )

        crud_event.save()
    except:
        pass

def user_logged_in(sender, request, user, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.LOGIN, username=user.username, user=user)
        login_event.save()
    except:
        pass

def user_logged_out(sender, request, user, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.LOGOUT, username=user.username, user=user)
        login_event.save()
    except:
        pass

def user_login_failed(sender, credentials, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.FAILED, username=credentials['username'])
        login_event.save()
    except:
        pass

models_signals.post_save.connect(post_save)
models_signals.post_delete.connect(post_delete)
auth_signals.user_logged_in.connect(user_logged_in)
auth_signals.user_logged_out.connect(user_logged_out)
auth_signals.user_login_failed.connect(user_login_failed)
