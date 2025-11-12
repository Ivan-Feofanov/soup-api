import pytest
from ninja_extra import status

from kitchen.models import Ingredient


@pytest.mark.django_db
def test_list_ingredients(client, ingredient_factory):
    ings = ingredient_factory.create_batch(5)
    resp = client.get("/api/kitchen/ingredients/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    names = sorted(d["name"] for d in data)

    assert {ing.name for ing in ings} == set(names)


@pytest.mark.django_db
def test_create_ingredient(authenticated_client):
    url = "/api/kitchen/ingredients/"
    payload = {"name": "Sugar"}

    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["name"] == "Sugar"
    assert Ingredient.objects.filter(name="Sugar").exists()


@pytest.mark.parametrize("name", ["Sugar", "sugar", "SUGAR", "sugar ", " sugar"])
@pytest.mark.django_db
def test_create_ingredient_idempotent_by_name(authenticated_client, name):
    url = "/api/kitchen/ingredients/"
    payload = {"name": name}
    r1 = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    first_uid = r1.json()["uid"]

    # Posting same name should return existing ingredient (same uid)
    r2 = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )

    assert r2.status_code == status.HTTP_200_OK
    assert r2.json()["uid"] == first_uid
