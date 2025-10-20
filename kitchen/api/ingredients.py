from ninja import ModelSchema, Schema
from ninja_extra import api_controller, http_get, ControllerBase, http_post, status
from ninja_jwt.authentication import JWTAuth

from kitchen.models import Ingredient


class IngredientSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["uid", "name"]


class IngredientCreateSchema(Schema):
    name: str
    image: str | None = None


@api_controller("/kitchen/ingredients", tags=["Ingredients"])
class IngredientsController(ControllerBase):
    @http_get("/", response=list[IngredientSchema])
    def list_ingredients(self, request):
        return Ingredient.objects.all()

    @http_post(
        "/",
        response={
            status.HTTP_200_OK: IngredientSchema,
            status.HTTP_201_CREATED: IngredientSchema,
        },
        auth=JWTAuth(),
    )
    def create_ingredient(self, request, payload: IngredientCreateSchema):
        existing_ingredient = Ingredient.objects.filter(name=payload.name).first()
        if existing_ingredient:
            return status.HTTP_200_OK, existing_ingredient
        return status.HTTP_201_CREATED, Ingredient.objects.create(
            **payload.model_dump()
        )
