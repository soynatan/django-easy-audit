import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from easyaudit.models import RequestEvent
from easyaudit.request_auth import (
    RequestAuthAdapter,
    SessionAuthAdapter,
    get_request_user,
)

SESSION_ADAPTER = "easyaudit.request_auth.SessionAuthAdapter"
REQUEST_AUTH_ADAPTER = "easyaudit.request_auth.RequestAuthAdapter"


@pytest.fixture
def adapters(settings):
    settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [
        REQUEST_AUTH_ADAPTER,
        SESSION_ADAPTER,
    ]
    return settings


def token_header(username):
    return {"HTTP_AUTHORIZATION": f"Token {username}"}


@pytest.mark.django_db
class TestDefaultRequestAuth:
    """With the setting untouched, nothing about request logging changes."""

    def test_session_user_is_recorded(self, user, client):
        client.force_login(user)
        client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().user == user

    def test_token_user_is_not_recorded(self, user, client, username):
        resp = client.get(reverse("test_app:token-auth"), **token_header(username))
        assert resp.status_code == 200

        assert RequestEvent.objects.get().user is None

    def test_event_is_written_before_the_view_runs(self, client):
        resp = client.get(reverse("test_app:count-request-events"))

        assert resp.content == b"1"
        assert RequestEvent.objects.count() == 1


@pytest.mark.django_db
class TestConfiguredRequestAuth:
    def test_token_user_is_recorded(self, adapters, user, client, username):
        resp = client.get(reverse("test_app:token-auth"), **token_header(username))
        assert resp.status_code == 200

        assert RequestEvent.objects.get().user == user

    def test_session_user_is_recorded(self, adapters, user, client):
        client.force_login(user)
        client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().user == user

    def test_anonymous_request_has_no_user(self, adapters, client):
        client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().user is None

    def test_rejected_token_has_no_user(self, adapters, user, client):
        resp = client.get(reverse("test_app:token-auth"), **token_header("nobody"))
        assert resp.status_code == 401

        assert RequestEvent.objects.get().user is None

    def test_session_adapter_alone_ignores_the_token(
        self, settings, user, client, username
    ):
        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [SESSION_ADAPTER]
        client.get(reverse("test_app:token-auth"), **token_header(username))

        assert RequestEvent.objects.get().user is None

    def test_event_is_written_once_after_the_view_runs(self, adapters, client):
        resp = client.get(reverse("test_app:count-request-events"))

        assert resp.content == b"0"
        assert RequestEvent.objects.count() == 1

    def test_event_keeps_the_request_details(self, adapters, client):
        client.post(reverse("test_app:index") + "?a=1", REMOTE_ADDR="10.0.0.1")

        event = RequestEvent.objects.get()
        assert event.url == reverse("test_app:index")
        assert event.method == "POST"
        assert event.query_string == "a=1"
        assert event.remote_ip == "10.0.0.1"

    def test_unregistered_url_is_not_logged(self, adapters, admin_client):
        admin_client.get(reverse("admin:index"))

        assert RequestEvent.objects.count() == 0

    def test_anonymous_response_does_not_vary_on_cookie(self, adapters, client):
        resp = client.get(reverse("test_app:index"))

        assert "Cookie" not in resp.get("Vary", "")

    def test_session_response_does_not_vary_on_cookie(self, adapters, user, client):
        client.force_login(user)
        resp = client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().user == user
        assert "Cookie" not in resp.get("Vary", "")


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConfiguredRequestAuthASGI:
    async def test_token_user_is_recorded(
        self, adapters, async_user, async_client, username
    ):
        resp = await async_client.get(
            reverse("test_app:token-auth"),
            headers={"Authorization": f"Token {username}"},
        )
        assert resp.status_code == 200

        event = await RequestEvent.objects.select_related("user").aget()
        assert event.user == async_user

    async def test_anonymous_request_has_no_user(self, adapters, async_client):
        await async_client.get(reverse("test_app:index"))

        event = await RequestEvent.objects.aget()
        assert event.user_id is None


@pytest.mark.django_db
class TestAdapters:
    def test_request_auth_adapter_needs_an_authenticated_user(self, user):
        request = RequestFactory().get("/")
        adapter = RequestAuthAdapter()
        assert adapter.get_user(request) is None

        # DRF's UNAUTHENTICATED_TOKEN can set `auth` on an anonymous request.
        request.user = AnonymousUser()
        request.auth = "anonymous-token"
        assert adapter.get_user(request) is None

        request.user = user
        assert adapter.get_user(request) == user

        request.auth = None
        assert adapter.get_user(request) is None

    def test_session_adapter_ignores_an_unknown_session(self, settings):
        request = RequestFactory().get("/")
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "missing"

        assert SessionAuthAdapter().get_user(request) is None

    def test_first_adapter_to_answer_wins(self, settings, user, django_user_model):
        other = django_user_model.objects.create_user("other", "o@example.com", "pw")

        class First:
            def get_user(self, request):
                return None

        class Second:
            def get_user(self, request):
                return user

        class Third:
            def get_user(self, request):
                return other

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [First, Second, Third]

        assert get_request_user(RequestFactory().get("/")) == user
