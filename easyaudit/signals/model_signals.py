import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import transaction
from django.db.models import signals
from django.utils import timezone
from django.utils.encoding import force_text

from easyaudit.middleware.easyaudit import get_current_request, \
    get_current_user
from easyaudit.models import CRUDEvent
from easyaudit.settings import REGISTERED_CLASSES, UNREGISTERED_CLASSES, \
    WATCH_MODEL_EVENTS, CRUD_DIFFERENCE_CALLBACKS
from easyaudit.utils import model_delta

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
def pre_save(sender, instance, raw, using, update_fields, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-save"""
    if raw:
        # Return if loading Fixtures
        return

    try:
        with transaction.atomic():
            if not should_audit(instance):
                return False
            try:
                object_json_repr = serializers.serialize("json", [instance])
            except Exception:
                # We need a better way for this to work. ManyToMany will fail on pre_save on create
                return None

            if instance.pk is None:
                created = True
            else:
                created = False

            # created or updated?
            if not created:
                old_model = sender.objects.get(pk=instance.pk)
                delta = model_delta(old_model, instance)
                changed_fields = json.dumps(delta)
                event_type = CRUDEvent.UPDATE

            # user
            try:
                user = get_current_user()
                # validate that the user still exists
                user = get_user_model().objects.get(pk=user.pk)
            except:
                user = None

            if isinstance(user, AnonymousUser):
                user = None

            # callbacks
            kwargs['request'] = get_current_request()  # make request available for callbacks
            create_crud_event = all(
                callback(instance, object_json_repr, created, raw, using, update_fields, **kwargs)
                for callback in CRUD_DIFFERENCE_CALLBACKS if callable(callback))
            # create crud event only if all callbacks returned True
            if create_crud_event and not created:
                c_t = ContentType.objects.get_for_model(instance)
                sid = transaction.savepoint()
                try:
                    with transaction.atomic():
                        crud_event = CRUDEvent.objects.create(
                            event_type=event_type,
                            object_repr=str(instance),
                            object_json_repr=object_json_repr,
                            changed_fields=changed_fields,
                            content_type_id=c_t.id,
                            object_id=instance.pk,
                            user_id=getattr(user, 'id', None),
                            datetime=timezone.now(),
                            user_pk_as_string=str(user.pk) if user else user
                        )
                except Exception as e:
                    logger.exception(
                        "easy audit had a pre-save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                            instance, instance.pk))
                    transaction.savepoint_rollback(sid)
    except Exception:
        logger.exception('easy audit had a pre-save exception.')


def post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-save"""
    if raw:
        # Return if loading Fixtures
        return

    try:
        with transaction.atomic():
            if not should_audit(instance):
                return False
            object_json_repr = serializers.serialize("json", [instance])

            # created or updated?
            if created:
                event_type = CRUDEvent.CREATE

            # user
            try:
                user = get_current_user()
                # validate that the user still exists
                user = get_user_model().objects.get(pk=user.pk)
            except:
                user = None

            if isinstance(user, AnonymousUser):
                user = None

            # callbacks
            kwargs['request'] = get_current_request()  # make request available for callbacks
            create_crud_event = all(callback(instance, object_json_repr,
                                             created, raw, using, update_fields, **kwargs)
                                    for callback in CRUD_DIFFERENCE_CALLBACKS
                                    if callable(callback))

            # create crud event only if all callbacks returned True
            if create_crud_event and created:
                c_t = ContentType.objects.get_for_model(instance)
                sid = transaction.savepoint()
                try:
                    with transaction.atomic():
                        crud_event = CRUDEvent.objects.create(
                            event_type=event_type,
                            object_repr=str(instance),
                            object_json_repr=object_json_repr,
                            content_type_id=c_t.id,
                            object_id=instance.pk,
                            user_id=getattr(user, 'id', None),
                            datetime=timezone.now(),
                            user_pk_as_string=str(user.pk) if user else user
                        )
                except Exception as e:
                    logger.exception(
                        "easy audit had a pre-save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                            instance, instance.pk))
                    transaction.savepoint_rollback(sid)
    except Exception:
        logger.exception('easy audit had a post-save exception.')


def _m2m_rev_field_name(model1, model2):
    """Gets the name of the reverse m2m accessor from `model1` to `model2`

    For example, if User has a ManyToManyField connected to Group,
    `_m2m_rev_field_name(Group, User)` retrieves the name of the field on
    Group that lists a group's Users. (By default, this field is called
    `user_set`, but the name can be overridden).
    """
    m2m_field_names = [
        rel.get_accessor_name() for rel in model1._meta.get_fields()
        if rel.many_to_many
           and rel.auto_created
           and rel.related_model == model2
    ]
    return m2m_field_names[0]


def m2m_changed(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#m2m-changed"""
    try:
        with transaction.atomic():
            if not should_audit(instance):
                return False

            if action not in ("post_add", "post_remove", "post_clear"):
                return False

            object_json_repr = serializers.serialize("json", [instance])

            if reverse:
                event_type = CRUDEvent.M2M_CHANGE_REV
                # add reverse M2M changes to event. must use json lib because
                # django serializers ignore extra fields.
                tmp_repr = json.loads(object_json_repr)

                m2m_rev_field = _m2m_rev_field_name(instance._meta.concrete_model, model)
                related_instances = getattr(instance, m2m_rev_field).all()
                related_ids = [r.pk for r in related_instances]

                tmp_repr[0]['m2m_rev_model'] = force_text(model._meta)
                tmp_repr[0]['m2m_rev_pks'] = related_ids
                tmp_repr[0]['m2m_rev_action'] = action
                object_json_repr = json.dumps(tmp_repr)
            else:
                event_type = CRUDEvent.M2M_CHANGE

            # user
            try:
                user = get_current_user()
                # validate that the user still exists
                user = get_user_model().objects.get(pk=user.pk)
            except:
                user = None

            if isinstance(user, AnonymousUser):
                user = None
            c_t = ContentType.objects.get_for_model(instance)
            sid = transaction.savepoint()

            try:
                with transaction.atomic():
                    crud_event = CRUDEvent.objects.create(
                        event_type=event_type,
                        object_repr=str(instance),
                        object_json_repr=object_json_repr,
                        content_type_id=c_t.id,
                        object_id=instance.pk,
                        user_id=getattr(user, 'id', None),
                        datetime=timezone.now(),
                        user_pk_as_string=str(user.pk) if user else user
                    )
            except Exception as e:
                logger.exception(
                    "easy audit had a pre-save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                        instance, instance.pk))
                transaction.savepoint_rollback(sid)
    except Exception:
        logger.exception('easy audit had an m2m-changed exception.')


def post_delete(sender, instance, using, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-delete"""
    try:
        with transaction.atomic():
            if not should_audit(instance):
                return False

            object_json_repr = serializers.serialize("json", [instance])

            # user
            try:
                user = get_current_user()
                # validate that the user still exists
                user = get_user_model().objects.get(pk=user.pk)
            except:
                user = None

            if isinstance(user, AnonymousUser):
                user = None
            c_t = ContentType.objects.get_for_model(instance)
            sid = transaction.savepoint()
            try:
                with transaction.atomic():
                    # crud event
                    crud_event = CRUDEvent.objects.create(
                        event_type=CRUDEvent.DELETE,
                        object_repr=str(instance),
                        object_json_repr=object_json_repr,
                        content_type_id=c_t.id,
                        object_id=instance.pk,
                        user_id=getattr(user, 'id', None),
                        datetime=timezone.now(),
                        user_pk_as_string=str(user.pk) if user else user
                    )

            except Exception as e:
                logger.exception(
                    "easy audit had a pre-save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                        instance, instance.pk))
                transaction.savepoint_rollback(sid)
    except Exception:
        logger.exception('easy audit had a post-delete exception.')


if WATCH_MODEL_EVENTS:
    signals.post_save.connect(post_save, dispatch_uid='easy_audit_signals_post_save')
    signals.pre_save.connect(pre_save, dispatch_uid='easy_audit_signals_pre_save')
    signals.m2m_changed.connect(m2m_changed, dispatch_uid='easy_audit_signals_m2m_changed')
    signals.post_delete.connect(post_delete, dispatch_uid='easy_audit_signals_post_delete')
