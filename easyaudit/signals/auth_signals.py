from django.contrib.auth import signals, get_user_model
from easyaudit.models import LoginEvent
from easyaudit.settings import WATCH_AUTH_EVENTS


def user_logged_in(sender, request, user, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.LOGIN, username=getattr(user, user.USERNAME_FIELD), user=user)
        login_event.save()
    except:
        pass


def user_logged_out(sender, request, user, **kwargs):
    try:
        login_event = LoginEvent(login_type=LoginEvent.LOGOUT, username=getattr(user, user.USERNAME_FIELD), user=user)
        login_event.save()
    except:
        pass


def user_login_failed(sender, credentials, **kwargs):
    try:
        user_model = get_user_model()
        login_event = LoginEvent(login_type=LoginEvent.FAILED, username=credentials[user_model.USERNAME_FIELD])
        login_event.save()
    except:
        pass


if WATCH_AUTH_EVENTS:
    signals.user_logged_in.connect(user_logged_in, dispatch_uid='easy_audit_signals_logged_in')
    signals.user_logged_out.connect(user_logged_out, dispatch_uid='easy_audit_signals_logged_out')
    signals.user_login_failed.connect(user_login_failed, dispatch_uid='easy_audit_signals_login_failed')