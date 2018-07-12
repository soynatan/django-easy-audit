from importlib import import_module

from django.apps.registry import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db.migrations import Migration
from django.db.migrations.recorder import MigrationRecorder
from django.utils import six

from easyaudit.models import CRUDEvent, LoginEvent, RequestEvent


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


# Should Django Easy Audit log model/auth/request events?
WATCH_AUTH_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS', True)
WATCH_MODEL_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS', True)
WATCH_REQUEST_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS', True)
REMOTE_ADDR_HEADER = getattr(settings, 'DJANGO_EASY_AUDIT_REMOTE_ADDR_HEADER', 'REMOTE_ADDR')

USE_LOG_ENTRY = getattr(settings, 'DJANGO_EASY_AUDIT_USE_LOG_ENTRY', True)


# Models which Django Easy Audit will not log.
# By default, all but some models will be audited.
# The list of excluded models can be overwritten or extended
# by defining the following settings in the project.
UNREGISTERED_CLASSES = [CRUDEvent, LoginEvent, RequestEvent, Migration, Session, Permission, ContentType, MigrationRecorder.Migration]
if USE_LOG_ENTRY:
    from django.contrib.admin.models import LogEntry
    UNREGISTERED_CLASSES += [LogEntry]
UNREGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_DEFAULT', UNREGISTERED_CLASSES)
UNREGISTERED_CLASSES.extend(getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA', []))
get_model_list(UNREGISTERED_CLASSES)


# Models which Django Easy Audit WILL log.
# If the following setting is defined in the project,
# only the listed models will be audited, and every other
# model will be excluded.
REGISTERED_CLASSES = getattr(settings, 'DJANGO_EASY_AUDIT_REGISTERED_CLASSES', [])
get_model_list(REGISTERED_CLASSES)


# URLs which Django Easy Audit will not log.
# By default, all but some URL requests will be logged.
# The list of excluded URLs can be overwritten or extended
# by defining the following settings in the project.
# Note: it is a list of regular expressions.
UNREGISTERED_URLS = [r'^/admin/', r'^/static/', r'^/favicon.ico$']
UNREGISTERED_URLS = getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_URLS_DEFAULT', UNREGISTERED_URLS)
UNREGISTERED_URLS.extend(getattr(settings, 'DJANGO_EASY_AUDIT_UNREGISTERED_URLS_EXTRA', []))


# By default all modules are listed in the admin.
# This can be changed with the following settings.
ADMIN_SHOW_MODEL_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_ADMIN_SHOW_MODEL_EVENTS', True)
ADMIN_SHOW_AUTH_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_ADMIN_SHOW_AUTH_EVENTS', True)
ADMIN_SHOW_REQUEST_EVENTS = getattr(settings, 'DJANGO_EASY_AUDIT_ADMIN_SHOW_REQUEST_EVENTS', True)


# project defined callbacks
CRUD_DIFFERENCE_CALLBACKS = []
CRUD_DIFFERENCE_CALLBACKS = getattr(settings, 'DJANGO_EASY_AUDIT_CRUD_DIFFERENCE_CALLBACKS', CRUD_DIFFERENCE_CALLBACKS)
# the callbacks could come in as an iterable of strings, where each string is the package.module.function
for idx, callback in enumerate(CRUD_DIFFERENCE_CALLBACKS):
    if not callable(callback):  # keep as is if it is callable
        CRUD_DIFFERENCE_CALLBACKS[idx] = getattr(import_module('.'.join(callback.split('.')[:-1])),
                                                 callback.split('.')[-1], None)

# Purge table optimization:
# If TRUNCATE_TABLE_SQL_STATEMENT is not empty, we use it as custom sql statement
# to speed up table truncation bypassing ORM, i.e.:
#   DJANGO_EASY_AUDIT_TRUNCATE_TABLE_SQL_STATEMENT = 'TRUNCATE TABLE "{db_table}"'  # for Postgresql
# Else we use Django Orm as follows:
#   model.objects.all().delete()
# which is however much costly when many rows are involved
TRUNCATE_TABLE_SQL_STATEMENT = getattr(settings, 'DJANGO_EASY_AUDIT_TRUNCATE_TABLE_SQL_STATEMENT', '')
