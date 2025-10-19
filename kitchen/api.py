import uuid

from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from ninja import Schema, ModelSchema
from ninja_extra import api_controller, ControllerBase, http_get, http_post, http_patch
from ninja_extra.exceptions import PermissionDenied
from ninja_jwt.authentication import JWTAuth

from kitchen.models import Recipe, Ingredient, Unit, RecipeIngredient
from users.models import CustomUser


class IngredientSchema(ModelSchema):
    class Meta:
        model = Ingredient
        fields = ["uid", "name"]


class UnitSchema(ModelSchema):
    class Meta:
        model = Unit
        fields = ["uid", "abbreviation", "name"]


class IngredientCreateSchema(Schema):
    name: str
    image: str | None = None


class IngredientInRecipeCreateSchema(Schema):
    ingredient_uid: uuid.UUID
    unit_uid: uuid.UUID | None = None
    quantity: float | None = None
    notes: str | None = None


class IngredientInRecipeSchema(ModelSchema):
    ingredient: IngredientSchema
    unit: UnitSchema | None = None

    class Meta:
        model = RecipeIngredient
        fields = ["uid", "ingredient", "unit", "quantity", "notes"]


class AuthorSchema(ModelSchema):
    class Meta:
        model = CustomUser
        fields = ["uid", "email", "username", "handler"]


class RecipeSchema(ModelSchema):
    class Meta:
        model = Recipe
        fields = "__all__"

    ingredients: list[IngredientInRecipeSchema] = []
    author: AuthorSchema | None = None

    @staticmethod
    def resolve_ingredients(recipe: Recipe):
        return recipe.recipeingredient_set.all()


class RecipeCreateSchema(Schema):
    title: str
    description: str
    image: str | None = None
    notes: str | None = None
    instructions: list[str]
    ingredients: list[IngredientInRecipeCreateSchema]


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

    @http_post("/ingredients/", response=IngredientSchema, auth=JWTAuth())
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
                title=payload.title,
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

    @http_patch(
        "/recipes/{uuid:uid}",
        response=RecipeSchema,
        auth=JWTAuth(),
    )
    def update_recipe(self, request, uid: uuid.UUID, payload: RecipeCreateSchema):
        recipe = get_object_or_404(Recipe, uid=uid)
        if recipe.author != request.user:
            raise PermissionDenied()
        recipe_payload = payload.model_dump()
        _ = recipe_payload.pop("ingredients")
        if payload.ingredients:
            recipe.recipeingredient_set.all().delete()
            for ingredient in payload.ingredients:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient_id=ingredient.ingredient_uid,
                    unit_id=ingredient.unit_uid,
                    quantity=ingredient.quantity,
                )
        for field, value in recipe_payload.items():
            if value is not None:
                setattr(recipe, field, value)
        recipe.save()
        recipe.refresh_from_db()
        return recipe
