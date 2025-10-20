import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken

from users.models import CustomUser


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def password():
    return "pass1234!"


@pytest.fixture
def user(password):
    return CustomUser.objects.create_user(
        email="user@example.com",
        password=password,
        username="john",
        handler="johnny",
    )


@pytest.fixture
def other_user(password):
    return CustomUser.objects.create_user(
        email="other@example.com",
        password=password,
        username="other",
        handler="other",
    )


@pytest.fixture
def get_token():
    def _get(user: CustomUser) -> str:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    return _get


@pytest.fixture
def token(user, get_token):
    return get_token(user)
