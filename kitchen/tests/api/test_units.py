import pytest
from ninja_extra import status

from kitchen.models import Unit


@pytest.mark.django_db
def test_list_units(client, unit_g, unit_ml):
    resp = client.get("/api/kitchen/units/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    abbrevs = [d["abbreviation"] for d in data]

    assert "g" in abbrevs
    assert "ml" in abbrevs


@pytest.mark.django_db
def test_create_unit(authenticated_client):
    url = "/api/kitchen/units/"
    payload = {"name": "Sugar", "abbreviation": "sg"}
    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_201_CREATED

    assert Unit.objects.filter(name="Sugar").exists()
    assert Unit.objects.filter(abbreviation="sg").exists()


@pytest.mark.django_db
def test_create_unit_idempotent_by_abbreviation(authenticated_client, unit_g):
    url = "/api/kitchen/units/"
    payload = {"name": "Sugar", "abbreviation": "g"}
    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["abbreviation"] == "g"
    assert Unit.objects.filter(abbreviation="g").count() == 1


@pytest.mark.parametrize("name", ["gram", "Gram", "gram ", " gram"])
@pytest.mark.django_db
def test_create_unit_idempotent_by_name(authenticated_client, unit_g, name: str):
    url = "/api/kitchen/units/"
    payload = {"name": name, "abbreviation": "sg"}
    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == unit_g.name
