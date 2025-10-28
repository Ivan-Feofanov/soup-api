import pytest
from ninja_jwt.tokens import RefreshToken


@pytest.mark.django_db
def test_social_login_invalid_code_returns_400(client):
    # Arrange: invalid code should be rejected by backend and return 400
    url = "/api/auth/login/google-oauth2/"
    payload = {"code": "invalid-code", "redirect_uri": "http://localhost/callback"}

    # Act
    resp = client.post(url, data=payload, content_type="application/json")

    # Assert
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("error") or data.get("detail")


@pytest.mark.django_db
def test_social_login_valid_code_returns_200(client, user, mocker):
    # Arrange: valid code should be accepted by backend and return 200
    load_backend_mock = mocker.patch("users.api.auth.load_backend")
    load_backend_mock.return_value.complete.return_value = user
    url = "/api/auth/login/google-oauth2/"
    payload = {"code": "valid-code", "redirect_uri": "http://localhost/callback"}

    # Act
    resp = client.post(url, data=payload, content_type="application/json")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.django_db
def test_refresh_token_valid_refresh_token_returns_200(client, user):
    # Arrange: valid refresh token should return 200
    refresh = RefreshToken.for_user(user)
    url = "/api/auth/token/refresh/"
    payload = {"refresh_token": str(refresh)}

    # Act
    resp = client.post(url, data=payload, content_type="application/json")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.django_db
def test_refresh_token_invalid_refresh_token_returns_400(client):
    # Arrange: invalid refresh token should return 400
    url = "/api/auth/token/refresh/"
    payload = {"refresh_token": "invalid-refresh-token"}

    # Act
    resp = client.post(url, data=payload, content_type="application/json")

    # Assert
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("error") or data.get("detail")
