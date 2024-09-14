# ruff: noqa: PLR0913
import json
import logging
from functools import partial

from django.conf import settings
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import signals
from django.utils.encoding import force_str

from easyaudit.middleware.easyaudit import get_current_request
from easyaudit.models import CRUDEvent
from easyaudit.settings import (
    CRUD_DIFFERENCE_CALLBACKS,
    REGISTERED_CLASSES,
    UNREGISTERED_CLASSES,
    WATCH_MODEL_EVENTS,
)
from easyaudit.utils import model_delta, should_propagate_exceptions

from .crud_flows import (
    m2m_changed_crud_flow,
    post_delete_crud_flow,
    post_save_crud_flow,
    pre_save_crud_flow,
)

logger = logging.getLogger(__name__)


def should_audit(instance):
    """Return True or False to indicate whether the instance should be audited."""
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


def call_callbacks(
    instance, object_json_repr, created, raw, using, update_fields, **kwargs
) -> bool:
    kwargs["request"] = get_current_request()  # Make request available in callbacks

    return all(
        callback(
            instance,
            object_json_repr,
            created,
            raw,
            using,
            update_fields,
            **kwargs,
        )
        for callback in CRUD_DIFFERENCE_CALLBACKS
        if callable(callback)
    )


def handle_signal_exception(signal):
    logger.exception(f"easy audit had a {signal} exception.")

    if should_propagate_exceptions():
        raise


def pre_save(sender, instance, raw, using, update_fields, **kwargs):
    if raw:
        # Return if loading Fixtures
        return None

    try:
        if not should_audit(instance):
            return False

        with transaction.atomic(using=using):
            try:
                object_json_repr = serializers.serialize("json", [instance])
            except Exception:
                # We need a better way for this to work. ManyToMany will fail on
                # pre_save on create
                return None

            # Determine if the instance is a create
            created = instance.pk is None or instance._state.adding

            # created or updated?
            delta = {}
            if not created:
                old_model = sender.objects.get(pk=instance.pk)
                delta = model_delta(old_model, instance)

                if not delta and getattr(
                    settings,
                    "DJANGO_EASY_AUDIT_CRUD_EVENT_NO_CHANGED_FIELDS_SKIP",
                    False,
                ):
                    return False

            # callbacks
            create_crud_event = call_callbacks(
                instance, object_json_repr, created, raw, using, update_fields, **kwargs
            )

            # Create crud event only if all callbacks returned True
            if create_crud_event and not created:
                crud_flow = partial(
                    pre_save_crud_flow,
                    instance=instance,
                    object_json_repr=object_json_repr,
                    changed_fields=json.dumps(delta),
                )

                if getattr(settings, "TEST", False):
                    crud_flow()
                else:
                    transaction.on_commit(crud_flow, using=using)
    except Exception:
        handle_signal_exception("pre_save")


def post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        # Return if loading Fixtures
        return None

    try:
        if not should_audit(instance):
            return False

        with transaction.atomic(using=using):
            object_json_repr = serializers.serialize("json", [instance])

            # callbacks
            create_crud_event = call_callbacks(
                instance, object_json_repr, created, raw, using, update_fields, **kwargs
            )

            # Create crud event only if all callbacks returned True
            if create_crud_event and created:
                crud_flow = partial(
                    post_save_crud_flow,
                    instance=instance,
                    object_json_repr=object_json_repr,
                )
                if getattr(settings, "TEST", False):
                    crud_flow()
                else:
                    transaction.on_commit(crud_flow, using=using)
    except Exception:
        handle_signal_exception("post_save")


def _m2m_rev_field_name(model1, model2):
    """Get the name of the reverse m2m accessor from `model1` to `model2`.

    For example, if User has a ManyToManyField connected to Group,
    `_m2m_rev_field_name(Group, User)` retrieves the name of the field on
    Group that lists a group's Users. (By default, this field is called
    `user_set`, but the name can be overridden).
    """
    m2m_field_names = [
        rel.get_accessor_name()
        for rel in model1._meta.get_fields()
        if rel.many_to_many and rel.auto_created and rel.related_model == model2
    ]
    return m2m_field_names[0]


def m2m_changed(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    try:
        if not should_audit(instance):
            return False
        if action not in ("post_add", "post_remove", "post_clear"):
            return False

        with transaction.atomic(using=using):
            object_json_repr = serializers.serialize("json", [instance])

            if reverse:
                reverse_actions = {
                    "post_add": CRUDEvent.M2M_ADD_REV,
                    "post_remove": CRUDEvent.M2M_REMOVE_REV,
                    "post_clear": CRUDEvent.M2M_CLEAR_REV,
                }
                event_type = reverse_actions.get(action, CRUDEvent.M2M_CHANGE_REV)

                # Add reverse M2M changes to event. Must use json lib because
                # django serializers ignore extra fields.
                tmp_repr = json.loads(object_json_repr)

                m2m_rev_field = _m2m_rev_field_name(instance._meta.concrete_model, model)
                related_instances = getattr(instance, m2m_rev_field).all()
                related_ids = [r.pk for r in related_instances]

                tmp_repr[0]["m2m_rev_model"] = force_str(model._meta)
                tmp_repr[0]["m2m_rev_pks"] = related_ids
                tmp_repr[0]["m2m_rev_action"] = action
                object_json_repr = json.dumps(tmp_repr, cls=DjangoJSONEncoder)
            else:
                forward_actions = {
                    "post_add": CRUDEvent.M2M_ADD,
                    "post_remove": CRUDEvent.M2M_REMOVE,
                    "post_clear": CRUDEvent.M2M_CLEAR,
                }
                event_type = forward_actions.get(action, CRUDEvent.M2M_CHANGE)

            crud_flow = partial(
                m2m_changed_crud_flow,
                action=action,
                model=model,
                instance=instance,
                pk_set=pk_set,
                event_type=event_type,
                object_json_repr=object_json_repr,
            )
            if getattr(settings, "TEST", False):
                crud_flow()
            else:
                transaction.on_commit(crud_flow, using=using)
    except Exception:
        handle_signal_exception("m2m-changed")


def post_delete(sender, instance, using, **kwargs):
    try:
        if not should_audit(instance):
            return False

        with transaction.atomic(using=using):
            object_json_repr = serializers.serialize("json", [instance])
            # instance.pk returns None if the changes are performed within a transaction
            object_id = instance.pk

            crud_flow = partial(
                post_delete_crud_flow,
                instance=instance,
                object_id=object_id,
                object_json_repr=object_json_repr,
            )
            if getattr(settings, "TEST", False):
                crud_flow()
            else:
                transaction.on_commit(
                    crud_flow,
                    using=using,
                )
    except Exception:
        handle_signal_exception("post-delete")


if WATCH_MODEL_EVENTS:
    signals.post_save.connect(post_save, dispatch_uid="easy_audit_signals_post_save")
    signals.pre_save.connect(pre_save, dispatch_uid="easy_audit_signals_pre_save")
    signals.m2m_changed.connect(m2m_changed, dispatch_uid="easy_audit_signals_m2m_changed")
    signals.post_delete.connect(post_delete, dispatch_uid="easy_audit_signals_post_delete")
