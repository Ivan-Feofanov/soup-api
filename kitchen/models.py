from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from shared.models import Common


class Unit(Common):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    abbreviation = models.CharField(max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.name


class Ingredient(Common):
    name = models.CharField(max_length=255, db_index=True)
    image = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Recipe(Common):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    instructions = ArrayField(models.TextField())

    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class RecipeIngredient(Common):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"
