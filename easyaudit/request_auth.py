"""Work out which user is behind a request, for ``RequestEvent``.

By default the user is read from the session cookie when the request starts, which
is all that is known before any view runs. Projects that authenticate inside the
view (Django REST framework and similar) can list adapters in
``DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS``; the request is then logged by
``EasyAuditMiddleware`` after the response, when the result of authentication is
available on the request.
"""

from functools import cache
from importlib import import_module

from django.conf import settings
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string


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

    def get_user(self, request):
        if getattr(request, "auth", None) is None:
            return None

        # DRF's UNAUTHENTICATED_TOKEN can set `auth` on an anonymous request.
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return user


def adapters_configured():
    """Whether the project has set ``DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS``."""
    return getattr(settings, "DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS", None) is not None


@cache
def _load_adapter(adapter):
    if isinstance(adapter, str):
        adapter = import_string(adapter)
    return adapter()


def get_request_user(request):
    """Return the user from the first configured adapter that names one, or None."""
    for adapter in settings.DJANGO_EASY_AUDIT_REQUEST_AUTH_ADAPTERS:
        user = _load_adapter(adapter).get_user(request)
        if user is not None:
            return user
    return None
