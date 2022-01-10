import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import signals
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.module_loading import import_string

from easyaudit.middleware.easyaudit import get_current_request, \
    get_current_user
from easyaudit.models import CRUDEvent
from easyaudit.settings import REGISTERED_CLASSES, UNREGISTERED_CLASSES, \
    WATCH_MODEL_EVENTS, CRUD_DIFFERENCE_CALLBACKS, LOGGING_BACKEND, \
    DATABASE_ALIAS
from easyaudit.utils import get_m2m_field_name, model_delta

logger = logging.getLogger(__name__)
audit_logger = import_string(LOGGING_BACKEND)()


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
        with transaction.atomic(using=using):
            if not should_audit(instance):
                return False
            try:
                object_json_repr = serializers.serialize("json", [instance])
            except Exception:
                # We need a better way for this to work. ManyToMany will fail on pre_save on create
                return None

            # Determine if the instance is a create
            created = instance.pk is None or instance._state.adding

            # created or updated?
            if not created:
                old_model = sender.objects.get(pk=instance.pk)
                delta = model_delta(old_model, instance)
                if not delta and getattr(settings, "DJANGO_EASY_AUDIT_CRUD_EVENT_NO_CHANGED_FIELDS_SKIP", False):
                    return False
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

                def crud_flow():
                    try:
                        # atomicity based on the easyaudit database alias
                        with transaction.atomic(using=DATABASE_ALIAS):
                            crud_event = audit_logger.crud({
                                'event_type': event_type,
                                'object_repr': str(instance),
                                'object_json_repr': object_json_repr,
                                'changed_fields': changed_fields,
                                'content_type_id': c_t.id,
                                'object_id': instance.pk,
                                'user_id': getattr(user, 'id', None),
                                'datetime': timezone.now(),
                                'user_pk_as_string': str(user.pk) if user else user
                            })
                    except Exception as e:
                        try:
                            logger.exception(
                                "easy audit had a pre_save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                                    instance, instance.pk))
                        except Exception:
                            pass
                if getattr(settings, "TEST", False):
                    crud_flow()
                else:
                    transaction.on_commit(crud_flow, using=using)
    except Exception:
        logger.exception('easy audit had a pre-save exception.')


def post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-save"""
    if raw:
        # Return if loading Fixtures
        return

    try:
        with transaction.atomic(using=using):
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

                def crud_flow():
                    try:
                        with transaction.atomic(using=DATABASE_ALIAS):
                            crud_event = audit_logger.crud({
                                'event_type': event_type,
                                'object_repr': str(instance),
                                'object_json_repr': object_json_repr,
                                'content_type_id': c_t.id,
                                'object_id': instance.pk,
                                'user_id': getattr(user, 'id', None),
                                'datetime': timezone.now(),
                                'user_pk_as_string': str(user.pk) if user else user
                            })
                    except Exception as e:
                        try:
                            logger.exception(
                                "easy audit had a post_save exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                                    instance, instance.pk))
                        except Exception:
                            pass
                if getattr(settings, "TEST", False):
                    crud_flow()
                else:
                    transaction.on_commit(crud_flow, using=using)
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
        with transaction.atomic(using=using):
            if not should_audit(instance):
                return False

            if action not in ("post_add", "post_remove", "post_clear"):
                return False

            object_json_repr = serializers.serialize("json", [instance])

            if reverse:
                if action == 'post_add':
                    event_type = CRUDEvent.M2M_ADD_REV
                elif action == 'post_remove':
                    event_type = CRUDEvent.M2M_REMOVE_REV
                elif action == 'post_clear':
                    event_type = CRUDEvent.M2M_CLEAR_REV
                else:
                    event_type = CRUDEvent.M2M_CHANGE_REV  # just in case

                # add reverse M2M changes to event. must use json lib because
                # django serializers ignore extra fields.
                tmp_repr = json.loads(object_json_repr)

                m2m_rev_field = _m2m_rev_field_name(instance._meta.concrete_model, model)
                related_instances = getattr(instance, m2m_rev_field).all()
                related_ids = [r.pk for r in related_instances]

                tmp_repr[0]['m2m_rev_model'] = force_str(model._meta)
                tmp_repr[0]['m2m_rev_pks'] = related_ids
                tmp_repr[0]['m2m_rev_action'] = action
                object_json_repr = json.dumps(tmp_repr)
            else:
                if action == 'post_add':
                    event_type = CRUDEvent.M2M_ADD
                elif action == 'post_remove':
                    event_type = CRUDEvent.M2M_REMOVE
                elif action == 'post_clear':
                    event_type = CRUDEvent.M2M_CLEAR
                else:
                    event_type = CRUDEvent.M2M_CHANGE  # just in case

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

            def crud_flow():
                try:
                    if action == "post_clear":
                        changed_fields = []
                    else:
                        changed_fields = json.dumps({get_m2m_field_name(model, instance): list(pk_set)}, cls=DjangoJSONEncoder)
                    with transaction.atomic(using=DATABASE_ALIAS):
                        crud_event = audit_logger.crud({
                            'event_type': event_type,
                            'object_repr': str(instance),
                            'object_json_repr': object_json_repr,
                            'changed_fields': changed_fields,
                            'content_type_id': c_t.id,
                            'object_id': instance.pk,
                            'user_id': getattr(user, 'id', None),
                            'datetime': timezone.now(),
                            'user_pk_as_string': str(user.pk) if user else user
                        })
                except Exception as e:
                    try:
                        logger.exception(
                            "easy audit had a m2m_changed exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                                instance, instance.pk))
                    except Exception:
                        pass

            if getattr(settings, "TEST", False):
                crud_flow()
            else:
                transaction.on_commit(crud_flow, using=using)
    except Exception:
        logger.exception('easy audit had an m2m-changed exception.')


def post_delete(sender, instance, using, **kwargs):
    """https://docs.djangoproject.com/es/1.10/ref/signals/#post-delete"""
    try:
        with transaction.atomic(using=using):
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

            # object id to be used later
            obj_id = instance.pk

            def crud_flow():
                try:
                    with transaction.atomic(using=DATABASE_ALIAS):
                        # crud event
                        crud_event = audit_logger.crud({
                            'event_type': CRUDEvent.DELETE,
                            'object_repr': str(instance),
                            'object_json_repr': object_json_repr,
                            'content_type_id': c_t.id,
                            'object_id': obj_id,
                            'user_id': getattr(user, 'id', None),
                            'datetime': timezone.now(),
                            'user_pk_as_string': str(user.pk) if user else user
                        })

                except Exception as e:
                    try:
                        logger.exception(
                            "easy audit had a post_delete exception on CRUDEvent creation. instance: {}, instance pk: {}".format(
                                instance, instance.pk))
                    except Exception:
                        pass

            if getattr(settings, "TEST", False):
                crud_flow()
            else:
                transaction.on_commit(crud_flow, using=using)
    except Exception:
        logger.exception('easy audit had a post-delete exception.')


if WATCH_MODEL_EVENTS:
    signals.post_save.connect(post_save, dispatch_uid='easy_audit_signals_post_save')
    signals.pre_save.connect(pre_save, dispatch_uid='easy_audit_signals_pre_save')
    signals.m2m_changed.connect(m2m_changed, dispatch_uid='easy_audit_signals_m2m_changed')
    signals.post_delete.connect(post_delete, dispatch_uid='easy_audit_signals_post_delete')
