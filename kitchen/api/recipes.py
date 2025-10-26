import uuid

from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from ninja import Schema, ModelSchema
from ninja_extra import (
    api_controller,
    ControllerBase,
    http_get,
    http_post,
    http_patch,
    status,
    http_delete,
)
from ninja_extra.exceptions import PermissionDenied
from ninja_jwt.authentication import JWTAuth

from kitchen.api.ingredients import IngredientSchema
from kitchen.api.units import UnitSchema
from kitchen.models import Recipe, RecipeIngredient, Instruction
from users.models import CustomUser


class InstructionSchema(ModelSchema):
    class Meta:
        model = Instruction
        fields = ["uid", "step", "description", "timer"]


class InstructionCreateSchema(ModelSchema):
    class Meta:
        model = Instruction
        fields = ["step", "description", "timer"]


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
    instructions: list[InstructionSchema] = []
    author: AuthorSchema | None = None

    @staticmethod
    def resolve_ingredients(recipe: Recipe):
        return recipe.recipeingredient_set.all()


class RecipeCreateSchema(Schema):
    title: str
    description: str
    image: str | None = None
    notes: str | None = None
    instructions: list[InstructionCreateSchema]
    ingredients: list[IngredientInRecipeCreateSchema]


@api_controller("/kitchen/recipes", tags=["Recipes"])
class RecipesController(ControllerBase):
    @http_get("/", response=list[RecipeSchema])
    def list_recipes(self, request):
        return (
            Recipe.objects.select_related("author")
            .prefetch_related(
                "recipeingredient_set__ingredient",
                "recipeingredient_set__unit",
            )
            .order_by("-updated_at")
        )

    @http_get("/{uuid:uid}", response=RecipeSchema)
    def get_recipe(self, request, uid: uuid.UUID):
        return get_object_or_404(Recipe, uid=uid)

    @http_post(
        "/",
        response={
            status.HTTP_201_CREATED: RecipeSchema,
            status.HTTP_400_BAD_REQUEST: dict,
        },
        auth=JWTAuth(),
    )
    def create_recipe(self, request, payload: RecipeCreateSchema):
        with atomic():
            recipe = Recipe.objects.create(
                author=request.user,
                title=payload.title,
                description=payload.description,
                notes=payload.notes,
                image=payload.image,
            )

            if payload.instructions:
                instructions_for_create = []
                for instruction in payload.instructions:
                    instructions_for_create.append(
                        Instruction(
                            recipe=recipe,
                            step=instruction.step,
                            description=instruction.description,
                            timer=instruction.timer,
                        )
                    )
                Instruction.objects.bulk_create(instructions_for_create)

            for ingredient in payload.ingredients:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient_id=ingredient.ingredient_uid,
                    unit_id=ingredient.unit_uid,
                    quantity=ingredient.quantity,
                )
            recipe.refresh_from_db()
            return status.HTTP_201_CREATED, recipe

    @http_patch(
        "/{uuid:uid}",
        response=RecipeSchema,
        auth=JWTAuth(),
    )
    def update_recipe(self, request, uid: uuid.UUID, payload: RecipeCreateSchema):
        recipe = get_object_or_404(Recipe, uid=uid)
        if recipe.author != request.user:
            raise PermissionDenied()
        recipe_payload = payload.model_dump()
        del recipe_payload["ingredients"]
        del recipe_payload["instructions"]
        if payload.instructions:
            instructions_for_create = []
            recipe.instructions.all().delete()
            for instruction in payload.instructions:
                instructions_for_create.append(
                    Instruction(
                        recipe=recipe,
                        step=instruction.step,
                        description=instruction.description,
                        timer=instruction.timer,
                    )
                )
            Instruction.objects.bulk_create(instructions_for_create)

        if payload.ingredients:
            recipe.recipeingredient_set.all().delete()
            ingredients_for_create = []
            for ingredient in payload.ingredients:
                ingredients_for_create.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient_id=ingredient.ingredient_uid,
                        unit_id=ingredient.unit_uid,
                        quantity=ingredient.quantity,
                    )
                )
            RecipeIngredient.objects.bulk_create(ingredients_for_create)

        for field, value in recipe_payload.items():
            if value is not None:
                setattr(recipe, field, value)
        recipe.save()
        recipe.refresh_from_db()
        return recipe

    @http_delete(
        path="/{uuid:uid}", response={status.HTTP_204_NO_CONTENT: None}, auth=JWTAuth()
    )
    def delete_recipe(self, request, uid: uuid.UUID):
        recipe = get_object_or_404(Recipe, uid=uid)
        if recipe.author != request.user:
            raise PermissionDenied()
        recipe.delete()
        return status.HTTP_204_NO_CONTENT, None
