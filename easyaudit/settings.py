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

# unregistered classes
UNREGISTERED_CLASSES = [CRUDEvent, LoginEvent, Migration, LogEntry, Session, Permission, ContentType,
                        MigrationRecorder.Migration]
# see if the project settings differ
UNREGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_DEFAULT_UNREGISTERED_CLASSES', UNREGISTERED_CLASSES)
# if the project has classes that they don't want registered, but want the original set, but don't want to import them
# then they can use the APPEND setting.
UNREGISTERED_CLASSES.extend(getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_APPEND', []))

for idx, item in enumerate(UNREGISTERED_CLASSES):
    if isinstance(item, six.string_types):
        model_class = apps.get_model(item)
        UNREGISTERED_CLASSES[idx] = model_class

WATCH_LOGIN_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_LOGIN_EVENTS', True)

CRUD_DIFFERENCE_CALLBACKS = []
CRUD_DIFFERENCE_CALLBACKS = getattr(settings, 'DJANGO_EASY_AUDIT_CRUD_DIFFERENCE_CALLBACKS', CRUD_DIFFERENCE_CALLBACKS)
# the callbacks could come in as an iterable of strings, where each string is the package.module.function
for idx, callback in enumerate(CRUD_DIFFERENCE_CALLBACKS):
    if not callable(callback):  # keep as is if it is callable
        CRUD_DIFFERENCE_CALLBACKS[idx] = getattr(import_module('.'.join(callback.split('.')[:-1])),
                                                 callback.split('.')[-1], None)
