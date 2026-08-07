"""Auditing models whose default manager filters rows out. See issue #175."""

import pytest
from django.contrib.contenttypes.models import ContentType

from easyaudit.models import CRUDEvent
from tests.test_app.models import HidableModel


@pytest.fixture
def hidden_obj() -> HidableModel:
    """Return a saved instance that the default manager no longer returns.

    Hiding it is a plain `save()`: at that point the row is still visible, so
    it exercises no part of the behaviour under test.
    """
    obj = HidableModel.objects.create(name="visible")
    obj.hidden = True
    obj.save()

    assert not HidableModel.objects.filter(pk=obj.pk).exists()

    return obj


def crud_events(obj: HidableModel):
    return CRUDEvent.objects.filter(
        object_id=obj.pk, content_type=ContentType.objects.get_for_model(obj)
    )


@pytest.mark.django_db
def test_update_of_hidden_row_is_audited(hidden_obj: HidableModel):
    """A row hidden by the default manager can still be saved and is audited."""
    crud_event_qs = crud_events(hidden_obj)
    crud_event_qs.delete()

    hidden_obj.name = "renamed while hidden"
    hidden_obj.save()

    assert crud_event_qs.count() == 1

    crud_event = crud_event_qs.first()
    assert crud_event.event_type == CRUDEvent.UPDATE
    assert "name" in crud_event.changed_fields


@pytest.mark.django_db
def test_restore_of_hidden_row_is_audited(hidden_obj: HidableModel):
    """Un-hiding a row (the soft-delete `restore()` case) is audited too."""
    crud_event_qs = crud_events(hidden_obj)
    crud_event_qs.delete()

    hidden_obj.hidden = False
    hidden_obj.save()

    assert HidableModel.objects.filter(pk=hidden_obj.pk).exists()
    assert crud_event_qs.count() == 1

    crud_event = crud_event_qs.first()
    assert crud_event.event_type == CRUDEvent.UPDATE
    assert "hidden" in crud_event.changed_fields
