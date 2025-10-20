import pytest
from ninja_extra import status

from kitchen.models import Ingredient


@pytest.mark.django_db
def test_list_ingredients(client, ing_flour, ing_water):
    resp = client.get("/api/kitchen/ingredients/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    names = sorted(d["name"] for d in data)

    assert {"Flour", "Water"}.issubset(set(names))


@pytest.mark.django_db
def test_create_ingredient(client, token):
    url = "/api/kitchen/ingredients/"
    payload = {"name": "Sugar"}

    resp = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["name"] == "Sugar"
    assert Ingredient.objects.filter(name="Sugar").exists()


@pytest.mark.parametrize("name", ["Sugar", "sugar", "SUGAR", "sugar ", " sugar"])
@pytest.mark.django_db
def test_create_ingredient_idempotent_by_name(client, token, name):
    url = "/api/kitchen/ingredients/"
    payload = {"name": name}
    r1 = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    first_uid = r1.json()["uid"]

    # Posting same name should return existing ingredient (same uid)
    r2 = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert r2.status_code == status.HTTP_200_OK
    assert r2.json()["uid"] == first_uid
