import logging

from django.contrib.auth import signals as auth_signals, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db.models import signals as models_signals
from django.utils import timezone

from .middleware.easyaudit import get_current_request, get_current_user
from .models import CRUDEvent, LoginEvent
from .settings import REGISTERED_CLASSES, UNREGISTERED_CLASSES, WATCH_LOGIN_EVENTS, CRUD_DIFFERENCE_CALLBACKS


logger = logging.getLogger(__name__)

def should_audit(instance):
    """Returns True or False to indicate whether the instance
    should be audited or not, depending on the project settings."""

    # do not audit any model listed in UNREGISTERED_CLASSES
    for unregistered_class in UNREGISTERED_CLASSES:
        if isinstance(instance, unregistered_class):
            return False

    # only audit models listed in REGISTERED_CLASSES (if it's set)
    if len(REGISTERED_CLASSES) > 0:
        for registered_class in REGISTERED_CLASSES:
            if isinstance(instance, registered_class):
                break
        else:
            return False

    # all good
    return True


# signals
def post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-save"""
    try:
        if not should_audit(instance):
            return False

        object_json_repr = serializers.serialize("json", [instance])

        # created or updated?
        if created:
            event_type = CRUDEvent.CREATE
        else:
            event_type = CRUDEvent.UPDATE

        # user
        try:
            user = get_current_user()
        except:
            user = None

        if isinstance(user, AnonymousUser):
            user = None

        # callbacks
        kwargs['request'] = get_current_request()  # make request available for callbacks
        create_crud_event = all(callback(instance, object_json_repr, created, raw, using, update_fields, **kwargs)
                                for callback in CRUD_DIFFERENCE_CALLBACKS if callable(callback))

        # create crud event only if all callbacks returned True
        if create_crud_event:
            crud_event = CRUDEvent.objects.create(
                event_type=event_type,
                object_repr=str(instance),
                object_json_repr=object_json_repr,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                user=user,
                datetime=timezone.now(),
                user_pk_as_string=str(user.pk) if user else user
            )

            crud_event.save()
    except Exception:
        logger.exception('easy audit had a post-save exception.')


def post_delete(sender, instance, using, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-delete"""
    try:
        if not should_audit(instance):
            return False

        object_json_repr = serializers.serialize("json", [instance])

        # user
        try:
            user = get_current_user()
        except:
            user = None

        if isinstance(user, AnonymousUser):
            user = None

        # crud event
        crud_event = CRUDEvent.objects.create(
            event_type=CRUDEvent.DELETE,
            object_repr=str(instance),
            object_json_repr=object_json_repr,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            user=user,
            datetime=timezone.now(),
            user_pk_as_string=str(user.pk) if user else user
        )

        crud_event.save()
    except Exception:
        logger.exception('easy audit had a post-delete exception.')


def user_logged_in(sender, request, user, **kwargs):
    try:

        login_event = LoginEvent(login_type=LoginEvent.LOGIN, username=getattr(user, user.USERNAME_FIELD), user=user)
        login_event.save()
    except:
        pass


def user_logged_out(sender, request, user, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.LOGOUT, username=getattr(user, user.USERNAME_FIELD), user=user)
        login_event.save()
    except:
        pass


def user_login_failed(sender, credentials, **kwargs):
    try:
        user_model = get_user_model()
        login_event = LoginEvent(login_type=LoginEvent.FAILED, username=credentials[user_model.USERNAME_FIELD])
        login_event.save()
    except:
        pass


models_signals.post_save.connect(post_save, dispatch_uid='easy_audit_signals_post_save')
models_signals.post_delete.connect(post_delete, dispatch_uid='easy_audit_signals_post_delete')

if WATCH_LOGIN_EVENTS:
    auth_signals.user_logged_in.connect(user_logged_in, dispatch_uid='easy_audit_signals_logged_in')
    auth_signals.user_logged_out.connect(user_logged_out, dispatch_uid='easy_audit_signals_logged_out')
    auth_signals.user_login_failed.connect(user_login_failed, dispatch_uid='easy_audit_signals_login_failed')
