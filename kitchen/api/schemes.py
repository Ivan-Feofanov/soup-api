import uuid

from ninja import ModelSchema, Schema

from kitchen.api.ingredients import IngredientSchema
from kitchen.api.units import UnitSchema

from kitchen.models import Instruction, RecipeIngredient, Recipe
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
        fields = ["uid", "username", "handler"]


class RecipeShortSchema(ModelSchema):
    class Meta:
        model = Recipe
        fields = [
            "uid",
            "title",
            "description",
            "image",
            "visibility",
            "author",
            "updated_at",
        ]

    author: AuthorSchema | None = None


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
    visibility: Recipe.Visibility = Recipe.Visibility.PRIVATE


class DraftSchema(Schema):
    uid: uuid.UUID | None = None
    title: str | None = None
    description: str | None = None
    image: str | None = None
    notes: str | None = None
    instructions: list[InstructionCreateSchema] | None = None
    ingredients: list[IngredientInRecipeCreateSchema] | None = None
    visibility: Recipe.Visibility = Recipe.Visibility.PRIVATE
