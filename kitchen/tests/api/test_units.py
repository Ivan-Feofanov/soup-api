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
def test_create_unit(client, token):
    url = "/api/kitchen/units/"
    payload = {"name": "Sugar", "abbreviation": "sg"}
    resp = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert resp.status_code == status.HTTP_201_CREATED

    assert Unit.objects.filter(name="Sugar").exists()
    assert Unit.objects.filter(abbreviation="sg").exists()


@pytest.mark.django_db
def test_create_unit_idempotent_by_abbreviation(client, token, unit_g):
    url = "/api/kitchen/units/"
    payload = {"name": "Sugar", "abbreviation": "g"}
    resp = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["abbreviation"] == "g"
    assert Unit.objects.filter(abbreviation="g").count() == 1


@pytest.mark.parametrize("name", ["gram", "Gram", "gram ", " gram"])
@pytest.mark.django_db
def test_create_unit_idempotent_by_name(client, token, unit_g, name: str):
    url = "/api/kitchen/units/"
    payload = {"name": name, "abbreviation": "sg"}
    resp = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == unit_g.name
