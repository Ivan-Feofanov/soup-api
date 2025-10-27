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
def access_token(user):
    """Returns a JWT access token for the default user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@pytest.fixture
def authenticated_client(client, access_token):
    """Returns a client with JWT authentication for the default user."""
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


@pytest.fixture
def get_authenticated_client(client):
    """Returns a function that creates an authenticated client for any user."""
    def _get(user: CustomUser):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        return client
    return _get
