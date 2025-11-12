import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken
from pytest_factoryboy import register, LazyFixture

from kitchen.tests.factories import (
    RecipeFactory,
    UnitFactory,
    IngredientFactory,
    InstructionFactory,
    ApplianceFactory,
    ApplianceTypeFactory,
    ManufacturerFactory,
    RecipeIngredientFactory,
)
from users.models import CustomUser
from users.tests.factories import CustomUserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def password():
    return "pass1234!"


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


register(CustomUserFactory, "user")
register(CustomUserFactory, "other_user")
register(UnitFactory)
register(IngredientFactory)
register(RecipeIngredientFactory)
register(InstructionFactory)
register(ApplianceFactory)
register(ApplianceTypeFactory)
register(ManufacturerFactory)
register(RecipeFactory, author=LazyFixture("user"))
register(
    RecipeFactory, "draft", is_draft=True, description="", author=LazyFixture("user")
)
