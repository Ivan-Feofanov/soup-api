import uuid
from ninja import Schema, ModelSchema

from kitchen.models import Appliance, ApplianceType, Manufacturer


class ManufacturerSchema(ModelSchema):
    class Meta:
        model = Manufacturer
        fields = ["uid", "name"]


class ManufacturerCreateSchema(Schema):
    name: str


class ApplianceTypeSchema(ModelSchema):
    class Meta:
        model = ApplianceType
        fields = ["uid", "name"]


class ApplianceTypeCreateSchema(Schema):
    name: str


class ApplianceSchema(ModelSchema):
    manufacturer: ManufacturerSchema
    type: ApplianceTypeSchema

    class Meta:
        model = Appliance
        fields = ["uid", "model", "manufacturer", "type"]


class ApplianceCreateSchema(Schema):
    model: str
    manufacturer_uid: uuid.UUID
    type_uid: uuid.UUID
