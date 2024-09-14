import json

import pytest
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.db import transaction
from django.urls import reverse
from django.utils.version import get_version
from pytest_django.asserts import assertInHTML

from easyaudit.middleware.easyaudit import clear_request, set_current_user
from easyaudit.models import CRUDEvent, RequestEvent
from tests.test_app.models import (
    BigIntForeignKeyModel,
    BigIntM2MModel,
    BigIntModel,
    ForeignKeyModel,
    M2MModel,
    Model,
    UUIDForeignKeyModel,
    UUIDM2MModel,
    UUIDModel,
)


@pytest.mark.django_db
def test_no_migrations(capsys: pytest.CaptureFixture):
    management.call_command("makemigrations", dry_run=True)

    captured = capsys.readouterr().out
    assert "No changes detected" in captured


def test_no_issues(capsys: pytest.CaptureFixture):
    management.call_command("check", fail_level="WARNING")

    captured: str = capsys.readouterr().out
    assert "System check identified no issues" in captured


@pytest.mark.parametrize(
    "model",
    [
        BigIntForeignKeyModel,
        BigIntM2MModel,
        BigIntModel,
        ForeignKeyModel,
        M2MModel,
        Model,
        UUIDForeignKeyModel,
        UUIDM2MModel,
        UUIDModel,
    ],
)
class TestDjangoCompat:
    def test_model_state(self, model):
        """Ensures models have the internal `_state` object."""
        model_instances = model()
        assert hasattr(model_instances, "_state")


@pytest.mark.django_db
class TestAuditModels:
    @pytest.fixture
    def model(self):
        return Model

    @pytest.fixture
    def fk_model(self):
        return ForeignKeyModel

    @pytest.fixture
    def m2m_model(self):
        return M2MModel

    @pytest.fixture
    def _audit_logger(self, monkeypatch):
        def _crud(*args, **kwargs):
            raise ValueError("Test exception")

        monkeypatch.setattr("easyaudit.signals.crud_flows.audit_logger.crud", _crud)

    def test_create_model(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        crud_event = crud_event_qs.first()
        data = json.loads(crud_event.object_json_repr)[0]
        assert data["fields"]["name"] == obj.name

    def test_fk_model(self, model, fk_model):
        obj = model.objects.create()
        obj_fk = fk_model(name="test", test_fk=obj)
        obj_fk.save()

        crud_event = CRUDEvent.objects.filter(
            object_id=obj_fk.id, content_type=ContentType.objects.get_for_model(obj_fk)
        ).first()
        data = json.loads(crud_event.object_json_repr)[0]
        assert str(data["fields"]["test_fk"]) == str(obj.id)

    def test_m2m_model(self, model, m2m_model):
        obj = model.objects.create()
        obj_m2m = m2m_model(name="test")
        obj_m2m.save()
        obj_m2m.test_m2m.add(obj)

        crud_event = CRUDEvent.objects.filter(
            object_id=obj_m2m.id,
            content_type=ContentType.objects.get_for_model(obj_m2m),
        ).first()
        data = json.loads(crud_event.object_json_repr)[0]
        assert [str(d) for d in data["fields"]["test_m2m"]] == [str(obj.id)]

    def test_m2m_clear(self, model, m2m_model):
        obj = model.objects.create()
        obj_m2m = m2m_model(name="test")
        obj_m2m.save()
        obj_m2m.test_m2m.add(obj)
        obj_m2m.test_m2m.clear()

        crud_event = CRUDEvent.objects.filter(
            object_id=obj_m2m.id,
            content_type=ContentType.objects.get_for_model(obj_m2m),
        ).first()
        data = json.loads(crud_event.object_json_repr)[0]
        assert [str(d) for d in data["fields"]["test_m2m"]] == []

    @pytest.mark.usefixtures("no_changed_fields_skip")
    def test_update_skip_no_changed_fields(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        obj.name = "changed name"
        obj.save()
        assert crud_event_qs.count() == 2

        last_change = crud_event_qs.first()
        assert "name" in last_change.changed_fields

    def test_update(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        obj.name = "changed name"
        obj.save()
        assert crud_event_qs.count() == 2

        last_change = crud_event_qs.first()
        assert "name" in last_change.changed_fields

    @pytest.mark.usefixtures("no_changed_fields_skip")
    def test_fake_update_skip_no_changed_fields(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        obj.save()
        assert crud_event_qs.count() == 1

    def test_fake_update(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        obj.save()
        assert crud_event_qs.count() == 2

    def test_delete(self, model):
        obj = model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        obj_id = obj.pk
        obj.delete()
        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj_id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 2

    @pytest.mark.django_db(transaction=True)
    def test_delete_transaction(self, model, settings):
        settings.TEST = False

        with transaction.atomic():
            obj = model.objects.create()
            model.objects.all().delete()

        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id,
            content_type=ContentType.objects.get_for_model(obj),
            event_type=CRUDEvent.CREATE,
        )
        assert crud_event_qs.count() == 1

        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id,
            content_type=ContentType.objects.get_for_model(obj),
            event_type=CRUDEvent.DELETE,
        )
        assert crud_event_qs.count() == 1

    @pytest.mark.usefixtures("_audit_logger")
    def test_propagate_exceptions(self, model, settings):
        with pytest.raises(ValueError, match="Test exception"):
            model.objects.create()

        settings.DJANGO_EASY_AUDIT_PROPAGATE_EXCEPTIONS = False
        try:
            model.objects.create()
        except ValueError:
            pytest.fail("Unexpected ValueError")


class TestAuditUUIDModels(TestAuditModels):
    @pytest.fixture
    def model(self):
        return UUIDModel

    @pytest.fixture
    def fk_model(self):
        return UUIDForeignKeyModel

    @pytest.fixture
    def m2m_model(self):
        return UUIDM2MModel


class TestAuditBigIntModels(TestAuditModels):
    @pytest.fixture
    def model(self):
        return BigIntModel

    @pytest.fixture
    def fk_model(self):
        return BigIntForeignKeyModel

    @pytest.fixture
    def m2m_model(self):
        return BigIntM2MModel


@pytest.mark.django_db
class TestMiddleware:
    def test_middleware_logged_in(self, user, client, username, password):
        client.login(username=username, password=password)
        client.post(reverse("test_app:create-obj"))
        assert Model.objects.count() == 1

        obj = Model.objects.all().first()
        crud_event = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        ).first()
        assert crud_event.user == user

    def test_middleware_not_logged_in(self, client):
        create_obj_url = reverse("test_app:create-obj")
        client.post(create_obj_url)
        assert Model.objects.count() == 1

        obj = Model.objects.all().first()
        crud_event = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        ).first()
        assert crud_event.user is None

    def test_manual_set_user(self, django_user_model, username, email, password):
        user = django_user_model.objects.create_user(username, email, password)
        set_current_user(user)
        obj = Model.objects.create()
        assert obj.id == 1

        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        crud_event = crud_event_qs.first()
        assert crud_event.user == user

        clear_request()
        obj = Model.objects.create()
        assert obj.id == 2

        crud_event_qs = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        )
        assert crud_event_qs.count() == 1

        crud_event = crud_event_qs.first()
        assert crud_event.user is None

    def test_middleware_logged_in_user_in_request(self, user, client):
        client.force_login(user)
        create_obj_url = reverse("test_app:create-obj")
        client.post(create_obj_url)
        assert Model.objects.count() == 1

        obj = Model.objects.first()
        crud_event = CRUDEvent.objects.filter(
            object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)
        ).first()
        assert crud_event.user == user


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestASGIRequestEvent:
    async def test_login(self, async_user, async_client, username, password):
        await sync_to_async(async_client.login)(username=username, password=password)
        assert await sync_to_async(RequestEvent.objects.count)() == 0

        resp = await async_client.get(reverse("test_app:index"))
        assert resp.status_code == 200

        qs = await sync_to_async(RequestEvent.objects.filter)(user=async_user)
        assert await sync_to_async(qs.exists)()

    async def test_remote_addr_default(self, async_client):
        assert await sync_to_async(RequestEvent.objects.count)() == 0

        resp = await async_client.request(
            method="GET",
            path=str(reverse("test_app:index")),
            server=("127.0.0.1", "80"),
            scheme="http",
            headers=[(b"host", b"testserver")],
            query_string="",
        )
        assert resp.status_code == 200

        event = await sync_to_async(RequestEvent.objects.get)(url=reverse("test_app:index"))
        assert event.remote_ip == "127.0.0.1"

    async def test_remote_addr_another(self, async_client):
        assert await sync_to_async(RequestEvent.objects.count)() == 0

        resp = await async_client.request(
            method="GET",
            path=str(reverse("test_app:index")),
            server=("127.0.0.1", "80"),
            client=("10.0.0.1", 111),
            scheme="http",
            headers=[(b"host", b"testserver")],
            query_string="",
        )
        assert resp.status_code == 200

        event = await sync_to_async(RequestEvent.objects.get)(url=reverse("test_app:index"))
        assert event.remote_ip == "10.0.0.1"


@pytest.mark.django_db
class TestWSGIRequestEvent:
    def test_login(self, user, client, username, password):
        client.login(username=username, password=password)
        assert RequestEvent.objects.count() == 0

        resp = client.get(reverse("test_app:index"))
        assert resp.status_code == 200

        assert RequestEvent.objects.get(user=user)


@pytest.mark.django_db
class TestAuditAdmin:
    @pytest.fixture
    def tag_name(self):
        return "summary" if get_version() >= "4.1" else "h3"

    def test_request_event_admin_no_users(self, admin_client, settings, tag_name):
        response = admin_client.get(reverse("admin:easyaudit_requestevent_changelist"))
        assert response.status_code == 200

        decoded_content = response.content.decode()
        for f in settings.DJANGO_EASY_AUDIT_REQUEST_EVENT_LIST_FILTER:
            assertInHTML(
                f"<{tag_name}>"
                f"By {RequestEvent._meta.get_field(f).verbose_name}"
                f"</{tag_name}>",
                decoded_content,
            )
