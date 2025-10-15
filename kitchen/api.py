import uuid

from django.shortcuts import get_object_or_404
from ninja import Schema, ModelSchema
from ninja_extra import api_controller, ControllerBase, http_get

from kitchen.models import Recipe
from users.models import CustomUser


class IngredientSchema(Schema):
    uid: uuid.UUID
    name: str
    unit: str | None = None
    quantity: float | None = None
    notes: str | None = None


class AuthorSchema(ModelSchema):
    class Meta:
        model = CustomUser
        fields = ["uid", "email", "username", "handler"]


class RecipeSchema(ModelSchema):
    class Meta:
        model = Recipe
        fields = "__all__"

    ingredients: list[IngredientSchema]
    author: AuthorSchema | None = None

    @staticmethod
    def resolve_ingredients(recipe: Recipe):
        try:
            result = [
                {
                    "uid": rec.uid,
                    "name": rec.ingredient.name,
                    "unit": rec.unit.abbreviation if rec.unit else None,
                    "quantity": rec.quantity,
                    "notes": rec.notes,
                }
                for rec in recipe.recipeingredient_set.all()
            ]
        except Exception as e:
            print(e)
            result = []
        return result


@api_controller("/kitchen", tags=["recipes"])
class KitchenController(ControllerBase):
    @http_get("/recipes/", response=list[RecipeSchema])
    def list_recipes(self, request):
        return Recipe.objects.select_related("author").prefetch_related(
            "recipeingredient_set__ingredient",
            "recipeingredient_set__unit",
        )

    @http_get("/recipes/{uuid:uid}", response=RecipeSchema)
    def get_recipe(self, request, uid: uuid.UUID):
        return get_object_or_404(Recipe, uid=uid)
