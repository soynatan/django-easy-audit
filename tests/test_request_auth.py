import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import reverse

from easyaudit.models import RequestEvent
from easyaudit.request_auth import (
    BaseAuthAdapter,
    RequestAuthAdapter,
    SessionAuthAdapter,
    get_request_auth,
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
    """The default adapter is the session one, and the event is written up front."""

    def test_session_user_is_recorded(self, user, client):
        client.force_login(user)
        client.get(reverse("test_app:index"))

        event = RequestEvent.objects.get()
        assert event.user == user
        assert event.auth_method == "session"

    def test_token_user_is_not_recorded(self, user, client, username):
        resp = client.get(reverse("test_app:token-auth"), **token_header(username))
        assert resp.status_code == 200

        event = RequestEvent.objects.get()
        assert event.user is None
        assert event.auth_method is None

    def test_anonymous_request_has_no_auth_method(self, client):
        client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().auth_method is None

    def test_event_is_written_before_the_view_runs(self, client):
        resp = client.get(reverse("test_app:count-request-events"))

        assert resp.content == b"1"
        assert RequestEvent.objects.count() == 1


@pytest.mark.django_db
class TestConfiguredRequestAuth:
    def test_token_user_is_recorded(self, adapters, user, client, username):
        resp = client.get(reverse("test_app:token-auth"), **token_header(username))
        assert resp.status_code == 200

        event = RequestEvent.objects.get()
        assert event.user == user
        assert event.auth_method == "token"

    def test_session_user_is_recorded(self, adapters, user, client):
        client.force_login(user)
        client.get(reverse("test_app:index"))

        event = RequestEvent.objects.get()
        assert event.user == user
        assert event.auth_method == "session"

    def test_anonymous_request_has_no_user(self, adapters, client):
        client.get(reverse("test_app:index"))

        event = RequestEvent.objects.get()
        assert event.user is None
        assert event.auth_method is None

    def test_rejected_token_has_no_user(self, adapters, user, client):
        resp = client.get(reverse("test_app:token-auth"), **token_header("nobody"))
        assert resp.status_code == 401

        event = RequestEvent.objects.get()
        assert event.user is None
        assert event.auth_method is None

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


@pytest.mark.django_db
class TestWriteTiming:
    """The event is written after the response only if an adapter needs that."""

    def test_session_adapter_alone_writes_before_the_view(self, settings, client):
        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [SESSION_ADAPTER]
        resp = client.get(reverse("test_app:count-request-events"))

        assert resp.content == b"1"
        assert RequestEvent.objects.count() == 1

    def test_session_adapter_alone_ignores_the_token(
        self, settings, user, client, username
    ):
        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [SESSION_ADAPTER]
        client.get(reverse("test_app:token-auth"), **token_header(username))

        assert RequestEvent.objects.get().user is None

    def test_adapter_that_does_not_say_is_run_after_the_view(
        self, settings, user, client, username
    ):
        class ReadsTheViewsUser:
            def get_user(self, request):
                return request.user if request.user.is_authenticated else None

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [ReadsTheViewsUser]
        resp = client.get(reverse("test_app:token-auth"), **token_header(username))
        assert resp.status_code == 200

        assert RequestEvent.objects.get().user == user

    def test_early_adapter_is_given_a_request(self, settings, client):
        seen = []

        class Early:
            requires_response = False

            def get_user(self, request):
                seen.append((request.method, request.path, request.COOKIES.get("a")))

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [Early]
        client.cookies["a"] = "1"
        client.get(reverse("test_app:index"))

        assert seen == [("GET", reverse("test_app:index"), "1")]


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
        assert event.auth_method == "token"

    async def test_anonymous_request_has_no_user(self, adapters, async_client):
        await async_client.get(reverse("test_app:index"))

        event = await RequestEvent.objects.aget()
        assert event.user_id is None

    async def test_early_adapter_is_given_a_request(self, settings, async_client):
        seen = []

        class Early:
            requires_response = False

            def get_user(self, request):
                seen.append((request.method, request.path))

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [Early]
        await async_client.get(reverse("test_app:index"))

        assert seen == [("GET", reverse("test_app:index"))]


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

        assert get_request_auth(RequestFactory().get("/")) == (user, None)

    def test_base_adapter_defaults_to_requiring_the_response(self):
        class TokenAdapter(BaseAuthAdapter):
            def get_user(self, request):
                return None

        assert TokenAdapter.requires_response is True
        assert SessionAuthAdapter.requires_response is False
        assert RequestAuthAdapter.requires_response is True

    def test_adapter_without_get_user_is_refused(self, settings, client):
        class NoGetUser:
            def get_usr(self, request):
                return None

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [NoGetUser]

        with pytest.raises(ImproperlyConfigured, match="NoGetUser"):
            client.get(reverse("test_app:index"))

    def test_base_adapter_subclass_must_override_get_user(self, settings, client):
        class Forgot(BaseAuthAdapter):
            pass

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [Forgot]

        with pytest.raises(ImproperlyConfigured, match="Forgot"):
            client.get(reverse("test_app:index"))

    def test_misconfigured_adapter_is_not_silenced(self, settings, client):
        """A bad adapter fails the request even when logging errors are swallowed."""

        class NoGetUser:
            pass

        settings.DJANGO_EASY_AUDIT_PROPAGATE_EXCEPTIONS = False
        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [NoGetUser]

        with pytest.raises(ImproperlyConfigured):
            client.get(reverse("test_app:index"))

    def test_adapter_names_its_own_auth_method(self, settings, user, client):
        class SsoAdapter(BaseAuthAdapter):
            requires_response = False
            auth_method = "sso"

            def get_user(self, request):
                return user

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [SsoAdapter]
        client.get(reverse("test_app:index"))

        assert RequestEvent.objects.get().auth_method == "sso"

    def test_adapter_without_an_auth_method_records_none(self, settings, user, client):
        class Unlabelled:
            requires_response = False

            def get_user(self, request):
                return user

        settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS = [Unlabelled]
        client.get(reverse("test_app:index"))

        event = RequestEvent.objects.get()
        assert event.user == user
        assert event.auth_method is None


@pytest.mark.django_db
class TestAuthMethodAdmin:
    def test_changelist_filters_by_auth_method(self, admin_client, user):
        RequestEvent.objects.create(url="/api/a/", method="GET", auth_method="token")
        RequestEvent.objects.create(url="/web/b/", method="GET", auth_method="session")
        RequestEvent.objects.create(url="/anon/c/", method="GET")

        resp = admin_client.get(
            reverse("admin:easyaudit_requestevent_changelist"),
            {"auth_method": "token"},
        )

        assert resp.status_code == 200
        assert [e.url for e in resp.context["cl"].result_list] == ["/api/a/"]
