import pytest
from django.conf import settings
from ninja_extra import status


@pytest.mark.django_db
def test_api_docs_accessible_for_staff(client, admin_user):
    # Arrange
    client.force_login(admin_user)

    # Act
    resp = client.get("/api/openapi.json")
    data = resp.json()

    # Assert
    assert resp.status_code == status.HTTP_200_OK
    assert data != {}
    assert data["paths"] != {}
    assert data["components"] != {}
    assert data["info"] != {}


@pytest.mark.django_db
def test_api_docs_accessible_for_token(client):
    # Arrange
    settings.OPENAPI_GENERATOR_TOKEN = "test-token"
    client.defaults["HTTP_X_Ninja_Token"] = "test-token"

    # Act
    resp = client.get("/api/openapi.json")
    data = resp.json()

    # Assert
    assert resp.status_code == status.HTTP_200_OK
    assert data != {}
    assert data["paths"] != {}
    assert data["components"] != {}
    assert data["info"] != {}


@pytest.mark.django_db
def test_api_docs_forbidden_for_invalid_token(client):
    # Arrange
    settings.OPENAPI_GENERATOR_TOKEN = "test-token"
    client.defaults["HTTP_X_Ninja_Token"] = "invalid-token"

    # Act
    resp = client.get("/api/openapi.json")

    # Assert
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_docs_forbidden_for_non_staff(client, user):
    # Arrange
    client.force_login(user)

    # Act
    resp = client.get("/api/openapi.json")

    # Assert
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_docs_forbidden_for_anonymous(client):
    # Act
    resp = client.get("/api/openapi.json")

    # Assert
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_docs_allow_for_debug(client):
    # Arrange
    settings.DEBUG = True

    # Act
    resp = client.get("/api/openapi.json")

    # Assert
    assert resp.status_code == status.HTTP_200_OK
