from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import NOT_PROVIDED, DateTimeField
from django.utils import timezone
from django.utils.encoding import smart_str


def default_get_datetimefield_value(obj, field):
    # DateTimeFields are timezone-aware, so we need to convert the field
    # to its naive form before we can accurately compare them for changes.
    try:
        value = field.to_python(getattr(obj, field.name, None))
        if value is not None and settings.USE_TZ and not timezone.is_naive(value):
            value = timezone.make_naive(value, timezone=timezone.utc)
    except ObjectDoesNotExist:
        value = field.default if field.default is not NOT_PROVIDED else None

    return value


RESOLVER_MAP = getattr(settings, "DJANGO_EASY_AUDIT_FIELD_VALUE_RESOLVER_MAP", dict())
RESOLVER_MAP.setdefault(DateTimeField, default_get_datetimefield_value)


def get_field_value(obj, field):
    """
    Gets the value of a given model instance field.
    :param obj: The model instance.
    :type obj: Model
    :param field: The field you want to find the value of.
    :type field: Any
    :return: The value of the field as a string.
    :rtype: str
    """
    try:
        for cls, resolver in RESOLVER_MAP.items():
            if isinstance(field, cls):
                return resolver(obj, field)
        value = smart_str(getattr(obj, field.name, None))
    except ObjectDoesNotExist:
        value = field.default if field.default is not NOT_PROVIDED else None

    return value


def model_delta(old_model, new_model):
    """
    Provides delta/difference between two models
    :param old: The old state of the model instance.
    :type old: Model
    :param new: The new state of the model instance.
    :type new: Model
    :return: A dictionary with the names of the changed fields as keys and a
             two tuple of the old and new field values
             as value.
    :rtype: dict
    """

    delta = {}
    fields = new_model._meta.fields
    for field in fields:
        old_value = get_field_value(old_model, field)
        new_value = get_field_value(new_model, field)
        if old_value != new_value:
            delta[field.name] = [smart_str(old_value),
                                 smart_str(new_value)]

    if len(delta) == 0:
        delta = None

    return delta


def get_m2m_field_name(model, instance):
    """
    Finds M2M field name on instance
    Called from m2m_changed signal
    :param model: m2m_changed signal model.
    :type model: Model
    :param instance:m2m_changed signal instance.
    :type new: Model
    :return: ManyToManyField name of instance related to model.
    :rtype: str
    """

    # When using Multi-table inheritance
    # https://docs.djangoproject.com/en/4.0/topics/db/models/#multi-table-inheritance
    # This might return None because the m2m relation is declared on the parent model
    for x in model._meta.related_objects:
        if x.related_model().__class__ == instance.__class__:
            return x.remote_field.name

    # instance._meta.many_to_many also holds the m2m relations defined on the parents
    for x in instance._meta.many_to_many:
        if x.related_model == model:
            return x.name


def get_model_queryset(model):
    queryset_method_name = getattr(model, "EASY_AUDIT_QUERYSET_METHOD", None)

    if not queryset_method_name:
        return model.objects.all()

    return getattr(model, queryset_method_name)()
