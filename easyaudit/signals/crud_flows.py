import contextlib
import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from easyaudit.middleware.easyaudit import get_current_user
from easyaudit.models import CRUDEvent
from easyaudit.settings import DATABASE_ALIAS, LOGGING_BACKEND
from easyaudit.utils import get_m2m_field_name, should_propagate_exceptions

logger = logging.getLogger(__name__)
audit_logger = import_string(LOGGING_BACKEND)()


def get_current_user_details():
    user_id = ""
    user_pk_as_string = ""

    with contextlib.suppress(Exception):
        user = get_current_user()
        if user and not isinstance(user, AnonymousUser):
            if getattr(settings, "DJANGO_EASY_AUDIT_CHECK_IF_REQUEST_USER_EXISTS", True):
                # validate that the user still exists
                user = get_user_model().objects.get(pk=user.pk)
            user_id, user_pk_as_string = user.id, str(user.pk)

    return user_id, user_pk_as_string


def log_event(event_type, instance, object_id, object_json_repr, **kwargs):
    user_id, user_pk_as_string = get_current_user_details()
    with transaction.atomic(using=DATABASE_ALIAS):
        audit_logger.crud(
            {
                "content_type_id": ContentType.objects.get_for_model(instance).id,
                "datetime": timezone.now(),
                "event_type": event_type,
                "object_id": object_id,
                "object_json_repr": object_json_repr or "",
                "object_repr": str(instance),
                "user_id": user_id,
                "user_pk_as_string": user_pk_as_string,
                **kwargs,
            }
        )


def handle_flow_exception(instance, signal):
    instance_str = ""
    with contextlib.suppress(Exception):
        instance_str = f" instance: {instance}, instance pk: {instance.pk}"

    logger.exception(
        f"easy audit had a {signal} exception on CRUDEvent creation.{instance_str}"
    )
    if should_propagate_exceptions():
        raise


def pre_save_crud_flow(instance, object_json_repr, changed_fields):
    try:
        log_event(
            CRUDEvent.UPDATE,
            instance,
            instance.pk,
            object_json_repr,
            changed_fields=changed_fields,
        )
    except Exception:
        handle_flow_exception(instance, "pre_save")


def post_save_crud_flow(instance, object_json_repr):
    try:
        log_event(
            CRUDEvent.CREATE,
            instance,
            instance.pk,
            object_json_repr,
        )
    except Exception:
        handle_flow_exception(instance, "post_save")


def m2m_changed_crud_flow(  # noqa: PLR0913
    action, model, instance, pk_set, event_type, object_json_repr
):
    try:
        if action == "post_clear":
            changed_fields = []
        else:
            changed_fields = json.dumps(
                {get_m2m_field_name(model, instance): list(pk_set)},
                cls=DjangoJSONEncoder,
            )
        log_event(
            event_type,
            instance,
            instance.pk,
            object_json_repr,
            changed_fields=changed_fields,
        )
    except Exception:
        handle_flow_exception(instance, "m2m_changed")


def post_delete_crud_flow(instance, object_id, object_json_repr):
    try:
        log_event(
            CRUDEvent.DELETE,
            instance,
            object_id,
            object_json_repr,
        )

    except Exception:
        handle_flow_exception(instance, "post_delete")
