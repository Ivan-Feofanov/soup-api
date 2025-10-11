import uuid

from ninja import Schema, ModelSchema, Router

from kitchen.models import Recipe
from users.models import CustomUser

router = Router()


class IngredientSchema(Schema):
    uid: uuid.UUID
    name: str
    unit: str | None = None
    quantity: float | None = None
    notes: str | None = None


class AuthorSchema(ModelSchema):
    class Meta:
        model = CustomUser
        fields = ["uid", "email", "first_name", "last_name"]


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


@router.get("/recipes/", response=list[RecipeSchema])
def list_recipes(request):
    return Recipe.objects.select_related("author").prefetch_related(
        "recipeingredient_set__ingredient",
        "recipeingredient_set__unit",
    )
