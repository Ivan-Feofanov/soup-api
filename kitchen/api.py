import uuid

from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from ninja import Schema, ModelSchema
from ninja_extra import api_controller, ControllerBase, http_get, http_post
from ninja_jwt.authentication import JWTAuth

from kitchen.models import Recipe, Ingredient, Unit, RecipeIngredient
from users.models import CustomUser


class IngredientSchema(Schema):
    uid: uuid.UUID
    name: str
    unit: str | None = None
    quantity: float | None = None
    notes: str | None = None


class IngredientCreateSchema(Schema):
    name: str
    image: str | None = None


class IngredientInRecipeSchema(Schema):
    ingredient_uid: uuid.UUID
    unit_uid: uuid.UUID | None = None
    quantity: float | None = None


class UnitSchema(Schema):
    uid: uuid.UUID
    abbreviation: str
    name: str


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


class RecipeCreateSchema(Schema):
    name: str
    description: str
    image: str | None = None
    notes: str | None = None
    instructions: list[str]
    ingredients: list[IngredientInRecipeSchema]


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

    @http_get("/ingredients/", response=list[IngredientSchema])
    def list_ingredients(self, request):
        return Ingredient.objects.all()

    @http_get("/units/", response=list[UnitSchema])
    def list_units(self, request):
        return Unit.objects.all()

    @http_post("/ingredients/", response=IngredientSchema)
    def create_ingredient(self, request, payload: IngredientCreateSchema):
        existing_ingredient = Ingredient.objects.filter(name=payload.name).first()
        if existing_ingredient:
            return existing_ingredient
        return Ingredient.objects.create(**payload.model_dump())

    @http_post("/recipes/", response=RecipeSchema, auth=JWTAuth())
    def create_recipe(self, request, payload: RecipeCreateSchema):
        with atomic():
            recipe = Recipe.objects.create(
                author=request.user,
                name=payload.name,
                description=payload.description,
                notes=payload.notes,
                instructions=payload.instructions,
            )
            for ingredient in payload.ingredients:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient_id=ingredient.ingredient_uid,
                    unit_id=ingredient.unit_uid,
                    quantity=ingredient.quantity,
                )
            recipe.refresh_from_db()
            return recipe
