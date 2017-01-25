
from django.conf import settings


# django unregistered classes
from django.db.migrations import Migration
from django.db.migrations.recorder import MigrationRecorder
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import six
from django.apps.registry import apps

from easyaudit.models import CRUDEvent, LoginEvent


# unregistered classes
UNREGISTERED_CLASSES = [CRUDEvent, LoginEvent, Migration, LogEntry, Session, Permission, ContentType, MigrationRecorder.Migration]

# see if the project settings differ
UNREGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_DEFAULT_UNREGISTERED_CLASSES', UNREGISTERED_CLASSES)
UNREGISTERED_CLASSES.extend(getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES', []))

for idx, item in enumerate(UNREGISTERED_CLASSES):
    if isinstance(item, six.string_types):
        model_class = apps.get_model(item)
        UNREGISTERED_CLASSES[idx] = model_class

WATCH_LOGIN_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_LOGIN_EVENTS', True)
