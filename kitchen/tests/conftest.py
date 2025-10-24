import pytest

from kitchen.models import Unit, Ingredient, Recipe, RecipeIngredient, Instruction


@pytest.fixture
def unit_g():
    return Unit.objects.create(name="Gram", abbreviation="g")


@pytest.fixture
def unit_ml():
    return Unit.objects.create(name="Milliliter", abbreviation="ml")


@pytest.fixture
def ing_flour():
    return Ingredient.objects.create(name="Flour")


@pytest.fixture
def ing_water():
    return Ingredient.objects.create(name="Water")


@pytest.fixture
def instructions(faker):
    return [
        Instruction(step=idx + 1, description=faker.sentence())
        for idx in range(faker.random_int(1, 5))
    ]


@pytest.fixture
def recipe(user, instructions, ing_flour, ing_water, unit_g, unit_ml):
    recipe = Recipe.objects.create(
        author=user,
        title="Bread",
        description="Simple bread",
    )
    recipe.instructions.set(instructions, bulk=False)
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing_flour,
        unit=unit_g,
        quantity=500,
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing_water,
        unit=unit_ml,
        quantity=300,
    )
    return recipe
