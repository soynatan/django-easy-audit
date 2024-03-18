from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from asgiref.sync import sync_to_async

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(autouse=True)
def test_settings(settings: SettingsWrapper) -> SettingsWrapper:
    settings.TEST = True

    return settings


@pytest.fixture
def no_changed_fields_skip(settings: SettingsWrapper) -> SettingsWrapper:
    settings.DJANGO_EASY_AUDIT_CRUD_EVENT_NO_CHANGED_FIELDS_SKIP = True

    return settings


@pytest.fixture
def username() -> str:
    return "joe@example.com"


@pytest.fixture
def password() -> str:
    return "password"


@pytest.fixture
def email() -> str:
    return "joe@example.com"


@pytest.fixture
def user(django_user_model: User, username: str, password: str, email: str) -> User:
    return django_user_model.objects.create_user(username, email, password)


@pytest.fixture
async def async_user(
    django_user_model: User, username: str, email: str, password: str
) -> User:
    return await sync_to_async(django_user_model.objects.create_user)(
        username, email, password
    )
