import uuid
from ninja_extra import api_controller, ControllerBase, http_get, http_post, status
from ninja_extra.exceptions import ValidationError
from ninja_jwt.authentication import JWTAuth, AsyncJWTAuth

from kitchen.api.appliances.schemes import ApplianceSchema, ApplianceCreateSchema
from kitchen.models import Appliance, Manufacturer, ApplianceType


@api_controller("/kitchen/appliances", tags=["Appliances"])
class AppliancesController(ControllerBase):
    @http_get("/", response=list[ApplianceSchema])
    async def list_appliances(
        self,
        request,
        manufacturer_uid: uuid.UUID | None = None,
        type_uid: uuid.UUID | None = None,
    ) -> list[Appliance]:
        """List appliances. Can be filtered by manufacturer and/or type."""
        qs = Appliance.objects.select_related("manufacturer", "type")
        filters = {}
        if manufacturer_uid:
            filters["manufacturer__uid"] = manufacturer_uid
        if type_uid:
            filters["type__uid"] = type_uid
        return [appliance async for appliance in qs.filter(**filters)]

    @http_post(
        "/",
        response={
            status.HTTP_200_OK: ApplianceSchema,
            status.HTTP_201_CREATED: ApplianceSchema,
        },
        auth=AsyncJWTAuth(),
    )
    async def create_appliance(self, request, payload: ApplianceCreateSchema):
        existing_appliance = await Appliance.objects.filter(
            model=payload.model,
            manufacturer__uid=payload.manufacturer_uid,
            type__uid=payload.type_uid,
        ).afirst()
        if existing_appliance:
            return status.HTTP_200_OK, existing_appliance
        try:
            manufacturer = await Manufacturer.objects.aget(uid=payload.manufacturer_uid)
        except Manufacturer.DoesNotExist:
            raise ValidationError(detail="Manufacturer does not exist", code="invalid")
        try:
            appliance_type = await ApplianceType.objects.aget(uid=payload.type_uid)
        except ApplianceType.DoesNotExist:
            raise ValidationError(
                detail="Appliance type does not exist", code="invalid"
            )
        appliance = await Appliance.objects.acreate(
            model=payload.model, manufacturer=manufacturer, type=appliance_type
        )
        return status.HTTP_201_CREATED, appliance
