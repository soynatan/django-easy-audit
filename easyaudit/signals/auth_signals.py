from django.contrib.auth import get_user_model, signals
from django.db import transaction
from django.utils.module_loading import import_string

from easyaudit.middleware.easyaudit import get_current_request
from easyaudit.models import LoginEvent
from easyaudit.settings import (
    DATABASE_ALIAS,
    LOGGING_BACKEND,
    REMOTE_ADDR_HEADER,
    WATCH_AUTH_EVENTS,
)
from easyaudit.utils import should_propagate_exceptions

audit_logger = import_string(LOGGING_BACKEND)()


def user_logged_in(sender, request, user, **kwargs):
    try:
        with transaction.atomic(using=DATABASE_ALIAS):
            audit_logger.login(
                {
                    "login_type": LoginEvent.LOGIN,
                    "username": getattr(user, user.USERNAME_FIELD),
                    "user_id": getattr(user, "id", None),
                    "remote_ip": request.META.get(REMOTE_ADDR_HEADER, ""),
                }
            )
    except Exception:
        if should_propagate_exceptions():
            raise


def user_logged_out(sender, request, user, **kwargs):
    try:
        with transaction.atomic(using=DATABASE_ALIAS):
            audit_logger.login(
                {
                    "login_type": LoginEvent.LOGOUT,
                    "username": getattr(user, user.USERNAME_FIELD),
                    "user_id": getattr(user, "id", None),
                    "remote_ip": request.META.get(REMOTE_ADDR_HEADER, ""),
                }
            )
    except Exception:
        if should_propagate_exceptions():
            raise


def user_login_failed(sender, credentials, **kwargs):
    try:
        with transaction.atomic(using=DATABASE_ALIAS):
            request = get_current_request()
            user_model = get_user_model()
            audit_logger.login(
                {
                    "login_type": LoginEvent.FAILED,
                    "username": credentials[user_model.USERNAME_FIELD],
                    "remote_ip": request.META.get(REMOTE_ADDR_HEADER, ""),
                }
            )
    except Exception:
        if should_propagate_exceptions():
            raise


if WATCH_AUTH_EVENTS:
    signals.user_logged_in.connect(
        user_logged_in, dispatch_uid="easy_audit_signals_logged_in"
    )
    signals.user_logged_out.connect(
        user_logged_out, dispatch_uid="easy_audit_signals_logged_out"
    )
    signals.user_login_failed.connect(
        user_login_failed, dispatch_uid="easy_audit_signals_login_failed"
    )
