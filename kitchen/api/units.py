from django.db.models import Q
from ninja import ModelSchema
from ninja_extra import api_controller, ControllerBase, http_get, http_post, status
from ninja_extra.permissions import IsAuthenticated

from kitchen.models import Unit


class UnitSchema(ModelSchema):
    class Meta:
        model = Unit
        fields = ["uid", "abbreviation", "name"]


@api_controller("/kitchen/units", tags=["Units"])
class UnitsController(ControllerBase):
    @http_get("/", response=list[UnitSchema])
    def list_units(self, request):
        return Unit.objects.all()

    @http_post(
        "/",
        response={status.HTTP_200_OK: UnitSchema, status.HTTP_201_CREATED: UnitSchema},
        permissions=[IsAuthenticated],
    )
    def create_unit(self, request, payload: UnitSchema):
        unit_name = payload.name.lower().strip()
        unit_abbreviation = payload.abbreviation.lower().strip()
        existing_unit = Unit.objects.filter(
            Q(name__iexact=unit_name) | Q(abbreviation__iexact=unit_abbreviation)
        ).first()
        if existing_unit:
            return status.HTTP_200_OK, existing_unit
        return status.HTTP_201_CREATED, Unit.objects.create(**payload.model_dump())
