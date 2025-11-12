import pytest
from ninja_extra import status

from kitchen.models import Unit


@pytest.mark.django_db
def test_list_units(client, unit_factory):
    units = unit_factory.create_batch(5)
    resp = client.get("/api/kitchen/units/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    abbrevs = [d["abbreviation"] for d in data]

    assert {unit.abbreviation for unit in units} == set(abbrevs)


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
def test_create_unit_idempotent_by_abbreviation(authenticated_client, unit):
    url = "/api/kitchen/units/"
    payload = {"name": "Sugar", "abbreviation": unit.abbreviation}
    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["abbreviation"] == unit.abbreviation
    assert Unit.objects.filter(abbreviation=unit.abbreviation).count() == 1


@pytest.mark.parametrize("name", ["gram", "Gram", "gram ", " gram"])
@pytest.mark.django_db
def test_create_unit_idempotent_by_name(authenticated_client, unit_factory, name: str):
    unit_g = unit_factory(name="gram")
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
