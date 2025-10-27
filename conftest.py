import pytest
from django.test import Client

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
def authenticated_client(client, user):
    """Returns a client with an authenticated session for the default user."""
    client.force_login(user)
    return client


@pytest.fixture
def get_authenticated_client(client):
    """Returns a function that creates an authenticated client for any user."""
    def _get(user: CustomUser):
        client.force_login(user)
        return client
    return _get
