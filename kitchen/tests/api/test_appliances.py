import pytest
import uuid6
from ninja_extra import status

from kitchen.models import Appliance, Manufacturer, ApplianceType


@pytest.mark.django_db
def test_list_appliances(client, appliance):
    resp = client.get("/api/kitchen/appliances/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    models = [d["model"] for d in data]

    assert appliance.model in models


@pytest.mark.django_db
def test_list_appliances_by_manufacturer(client, appliance):
    man2 = Manufacturer.objects.create(name="Other Manufacturer")
    Appliance.objects.create(
        model="Other Appliance", manufacturer=man2, type=appliance.type
    )

    resp = client.get(
        f"/api/kitchen/appliances/?manufacturer_uid={appliance.manufacturer.uid}"
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert len(data) == 1
    assert data[0]["model"] == appliance.model


@pytest.mark.django_db
def test_list_appliances_by_type(client, appliance):
    type2 = ApplianceType.objects.create(name="Other Type")
    Appliance.objects.create(
        model="Other Appliance", manufacturer=appliance.manufacturer, type=type2
    )

    resp = client.get(f"/api/kitchen/appliances/?type_uid={appliance.type.uid}")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert len(data) == 1
    assert data[0]["model"] == appliance.model


@pytest.mark.django_db
def test_list_appliances_by_manufacturer_and_type(client, appliance: Appliance):
    man2 = Manufacturer.objects.create(name="Other Manufacturer")
    type2 = ApplianceType.objects.create(name="Other Type")
    Appliance.objects.create(model="Other Appliance", manufacturer=man2, type=type2)
    Appliance.objects.create(
        model="Other Appliance 2", manufacturer=man2, type=appliance.type
    )

    resp = client.get(
        f"/api/kitchen/appliances/?manufacturer_uid={appliance.manufacturer.uid}&type_uid={appliance.type.uid}"
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert len(data) == 1
    assert data[0]["model"] == appliance.model


@pytest.mark.django_db
def test_create_appliance(authenticated_client, manufacturer, appliance_type):
    url = "/api/kitchen/appliances/"
    payload = {
        "model": "New Appliance",
        "manufacturer_uid": str(manufacturer.uid),
        "type_uid": str(appliance_type.uid),
    }

    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    db_appliance = Appliance.objects.get(uid=data["uid"])

    assert data["model"] == "New Appliance"
    assert db_appliance.model == "New Appliance"
    assert db_appliance.manufacturer == manufacturer
    assert db_appliance.type == appliance_type


@pytest.mark.django_db
def test_create_appliance_idempotent(
    authenticated_client, manufacturer, appliance_type, appliance
):
    url = "/api/kitchen/appliances/"
    payload = {
        "model": appliance.model,
        "manufacturer_uid": str(manufacturer.uid),
        "type_uid": str(appliance_type.uid),
    }

    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["uid"] == str(appliance.uid)


@pytest.mark.django_db
def test_create_appliance_validation_error(
    authenticated_client, manufacturer, appliance_type
):
    url = "/api/kitchen/appliances/"
    payload = {
        "model": "New Appliance",
        "manufacturer_uid": str(manufacturer.uid),
        "type_uid": str(uuid6.uuid7()),
    }

    resp = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json() == ["Appliance type does not exist"]
