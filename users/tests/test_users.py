import pytest


@pytest.mark.django_db
def test_me_requires_auth(client):
    # Arrange: no auth header
    url = "/api/users/me"

    # Act
    resp = client.get(url)

    # Assert
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_me_returns_current_user(authenticated_client, user):
    # Arrange
    url = "/api/users/me"

    # Act
    resp = authenticated_client.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["uid"] == str(user.uid)
    assert data["email"] == user.email
    assert data["username"] == user.username
    assert data["handler"] == user.handler


@pytest.mark.django_db
def test_update_user_self_success(authenticated_client, user):
    # Arrange
    url = f"/api/users/{user.uid}"
    payload = {
        "username": "Johnny",
        "handler": "chef-johnny",
        "avatar": "http://example.com/avatar.png",
    }

    # Act
    resp = authenticated_client.patch(
        url,
        data=payload,
        content_type="application/json",
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
def test_update_user_forbidden_when_other_uid(authenticated_client, user, other_user):
    # Arrange: user tries to update another user's profile
    url = f"/api/users/{other_user.uid}"
    payload = {"username": "hacker"}

    # Act
    resp = authenticated_client.patch(
        url,
        data=payload,
        content_type="application/json",
    )

    # Assert
    assert resp.status_code == 403
    assert (
        resp.json().get("detail")
        == "You do not have permission to perform this action."
    )


@pytest.mark.django_db
def test_update_user_validation_error_duplicate_handler(
    authenticated_client, user, other_user
):
    # Arrange: make other_user handler taken, then try to set same handler for user
    other_user.handler = "taken"
    other_user.save()
    url = f"/api/users/{user.uid}"
    payload = {"handler": "taken"}

    # Act
    resp = authenticated_client.patch(
        url,
        data=payload,
        content_type="application/json",
    )

    # Assert
    assert resp.status_code == 400
    body = resp.json()
    # Error format can be either top-level or nested under "detail" depending on exception handling
    errors = body.get("errors") or (body.get("detail") or {}).get("errors")
    assert isinstance(errors, dict)
    assert "handler" in errors
