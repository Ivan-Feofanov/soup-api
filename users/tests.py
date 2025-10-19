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


@pytest.mark.django_db
def test_me_requires_auth(client):
    # Arrange: no auth header
    url = "/api/users/me"

    # Act
    resp = client.get(url)

    # Assert
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_me_returns_current_user(client, user, get_token):
    # Arrange
    url = "/api/users/me"
    token = get_token(user)

    # Act
    resp = client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["uid"] == str(user.uid)
    assert data["email"] == user.email
    assert data["username"] == user.username
    assert data["handler"] == user.handler


@pytest.mark.django_db
def test_update_user_self_success(client, user, get_token):
    # Arrange
    url = f"/api/users/{user.uid}"
    token = get_token(user)
    payload = {
        "username": "Johnny",
        "handler": "chef-johnny",
        "avatar": "http://example.com/avatar.png",
    }

    # Act
    resp = client.patch(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == payload["username"]
    assert data["handler"] == payload["handler"]
    assert data["avatar"] == payload["avatar"]

    user.refresh_from_db()
    assert user.username == payload["username"]
    assert user.handler == payload["handler"]
    assert user.avatar == payload["avatar"]


@pytest.mark.django_db
def test_update_user_forbidden_when_other_uid(client, user, other_user, get_token):
    # Arrange: user tries to update another user's profile
    url = f"/api/users/{other_user.uid}"
    token = get_token(user)
    payload = {"username": "hacker"}

    # Act
    resp = client.patch(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    # Assert
    assert resp.status_code == 403
    assert (
        resp.json().get("detail")
        == "You do not have permission to perform this action."
    )


@pytest.mark.django_db
def test_update_user_validation_error_duplicate_handler(
    client, user, other_user, get_token
):
    # Arrange: make other_user handler taken, then try to set same handler for user
    other_user.handler = "taken"
    other_user.save()
    url = f"/api/users/{user.uid}"
    token = get_token(user)
    payload = {"handler": "taken"}

    # Act
    resp = client.patch(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    # Assert
    assert resp.status_code == 400
    body = resp.json()
    # Error format can be either top-level or nested under "detail" depending on exception handling
    errors = body.get("errors") or (body.get("detail") or {}).get("errors")
    assert isinstance(errors, dict)
    assert "handler" in errors


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
