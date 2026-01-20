import factory
from factory.django import DjangoModelFactory

from kitchen.models import (
    Appliance,
    ApplianceType,
    Ingredient,
    Instruction,
    Manufacturer,
    Recipe,
    RecipeIngredient,
    Unit,
)
from users.tests.factories import CustomUserFactory


class UnitFactory(DjangoModelFactory):
    class Meta:
        model = Unit
        django_get_or_create = ["name"]

    name = factory.Faker("word")
    abbreviation = factory.Faker("word")


class IngredientFactory(DjangoModelFactory):
    class Meta:
        model = Ingredient
        django_get_or_create = ["name"]

    name = factory.Faker("word")


class RecipeIngredientFactory(DjangoModelFactory):
    class Meta:
        model = RecipeIngredient

    recipe = factory.SubFactory("kitchen.tests.factories.RecipeFactory")
    ingredient = factory.SubFactory(IngredientFactory)
    unit = factory.SubFactory(UnitFactory)
    quantity = factory.Faker("random_int", min=1, max=1000)


class InstructionFactory(DjangoModelFactory):
    class Meta:
        model = Instruction

    recipe = factory.SubFactory("kitchen.tests.factories.RecipeFactory")
    step = factory.Sequence(lambda n: n)
    description = factory.Faker("sentence")


class ManufacturerFactory(DjangoModelFactory):
    class Meta:
        model = Manufacturer
        django_get_or_create = ["name"]

    name = factory.Faker("company")


class ApplianceTypeFactory(DjangoModelFactory):
    class Meta:
        model = ApplianceType
        django_get_or_create = ["name"]

    name = factory.Faker("word")


class ApplianceFactory(DjangoModelFactory):
    class Meta:
        model = Appliance
        django_get_or_create = ["model"]

    model = factory.Faker("word")
    manufacturer = factory.SubFactory(ManufacturerFactory)
    type = factory.SubFactory(ApplianceTypeFactory)


class RecipeFactory(DjangoModelFactory):
    class Meta:
        model = Recipe

    title = factory.Faker("sentence")
    author = factory.SubFactory(CustomUserFactory)
    visibility = Recipe.Visibility.PUBLIC
    is_draft = False
    description = factory.Faker("text")
    image = factory.Faker("image_url")
    notes = factory.Faker("text")
    slug = factory.Faker("slug")
    instructions = factory.RelatedFactoryList(InstructionFactory, "recipe", size=3)
    ingredients = factory.RelatedFactoryList(RecipeIngredientFactory, "recipe", size=3)

    @factory.post_generation
    def appliances(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # If a list of appliances is passed: RecipeFactory(appliances=[a1, a2])
            for appliance in extracted:
                self.appliances.add(appliance)
        else:
            for _ in range(3):
                self.appliances.add(ApplianceFactory())
