"""Work out which user is behind a request, for ``RequestEvent``.

``DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS`` lists the adapters asked for a request's
user; the first to name one wins. An adapter says whether it needs the view to have
run through ``requires_response``. When none does, the request is logged as it
starts. When any does, ``EasyAuditMiddleware`` logs it after the response instead,
when the result of the view's authentication is available on the request.
"""

from functools import cache
from importlib import import_module

from django.conf import settings
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

DEFAULT_ADAPTERS = ["easyaudit.request_auth.SessionAuthAdapter"]


def get_session_user(session_key):
    """Return the user logged in to the session with this key, or None."""
    # Imported here so this module can be imported before the app registry is ready.
    from django.contrib.sessions.models import Session

    session_engine = import_module(settings.SESSION_ENGINE)
    try:
        session = session_engine.SessionStore(session_key=session_key).load()
    except Session.DoesNotExist:
        session = None

    if session and AUTH_SESSION_KEY in session:
        user_id = session.get(AUTH_SESSION_KEY)
        try:
            return get_user_model().objects.get(id=user_id)
        except Exception:
            return None

    return None


class SessionAuthAdapter:
    """The user logged in to the session named by the request's session cookie.

    Reads the cookie and loads the session directly instead of going through
    ``request.session`` or ``request.user``: touching either marks the session as
    accessed, which makes Django add ``Vary: Cookie`` to the response.
    """

    requires_response = False

    def get_user(self, request):
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        if not session_key:
            return None
        return get_session_user(session_key)


class RequestAuthAdapter:
    """The user a view authenticated with a credential it left on ``request.auth``.

    Django REST framework authenticates inside the view and writes the result
    through to the underlying ``HttpRequest`` as ``request.user`` and
    ``request.auth``. ``auth`` is set for token-style authenticators (DRF's
    ``TokenAuthentication``, knox, simplejwt) and is ``None`` for session
    authentication and for a rejected credential.
    """

    requires_response = True

    def get_user(self, request):
        if getattr(request, "auth", None) is None:
            return None

        # DRF's UNAUTHENTICATED_TOKEN can set `auth` on an anonymous request.
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return user


@cache
def _load_adapter(adapter):
    if isinstance(adapter, str):
        adapter = import_string(adapter)
    return adapter()


def get_adapters():
    paths = getattr(settings, "DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS", DEFAULT_ADAPTERS)
    return [_load_adapter(path) for path in paths]


def adapters_require_response():
    """Whether any configured adapter needs the view to have run.

    An adapter that does not say is assumed to: after the response everything an
    adapter could read is on the request, so that is the safe reading.
    """
    return any(getattr(adapter, "requires_response", True) for adapter in get_adapters())


def get_request_user(request):
    """Return the user from the first configured adapter that names one, or None."""
    for adapter in get_adapters():
        user = adapter.get_user(request)
        if user is not None:
            return user
    return None
