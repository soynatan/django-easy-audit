from importlib import import_module

from django.apps.registry import apps
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db.migrations import Migration
from django.db.migrations.recorder import MigrationRecorder
from django.utils import six

from easyaudit.models import CRUDEvent, LoginEvent

def get_model_list(class_list):
    """
    Receives a list of strings with app_name.model_name format
    and turns them into classes. If an item is already a class
    it ignores it.
    """
    for idx, item in enumerate(class_list):
        if isinstance(item, six.string_types):
            model_class = apps.get_model(item)
            class_list[idx] = model_class


# default unregistered classes
UNREGISTERED_CLASSES = [CRUDEvent, LoginEvent, Migration, LogEntry, Session, Permission, ContentType,
                        MigrationRecorder.Migration]

# override default unregistered classes if defined in project settings
UNREGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_DEFAULT', UNREGISTERED_CLASSES)

# extra unregistered classes
UNREGISTERED_CLASSES.extend(getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA', []))
get_model_list(UNREGISTERED_CLASSES)

# register only the specified classes, excepting UNREGISTERED_CLASSES
REGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_REGISTERED_CLASSES', [])
get_model_list(REGISTERED_CLASSES)

# should login events be registered?
WATCH_LOGIN_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_LOGIN_EVENTS', True)

# project defined callbacks
CRUD_DIFFERENCE_CALLBACKS = []
CRUD_DIFFERENCE_CALLBACKS = getattr(settings, 'DJANGO_EASY_AUDIT_CRUD_DIFFERENCE_CALLBACKS', CRUD_DIFFERENCE_CALLBACKS)
# the callbacks could come in as an iterable of strings, where each string is the package.module.function
for idx, callback in enumerate(CRUD_DIFFERENCE_CALLBACKS):
    if not callable(callback):  # keep as is if it is callable
        CRUD_DIFFERENCE_CALLBACKS[idx] = getattr(import_module('.'.join(callback.split('.')[:-1])),
                                                 callback.split('.')[-1], None)
