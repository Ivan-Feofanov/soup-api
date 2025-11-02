from django.conf import settings
from django.db import models

from shared.models import Common


class Unit(Common):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    abbreviation = models.CharField(max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.name


class Instruction(Common):
    class Meta:
        ordering = ["step"]

    step = models.IntegerField()
    description = models.TextField()
    recipe = models.ForeignKey(
        "Recipe", on_delete=models.CASCADE, related_name="instructions"
    )
    timer = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.step} - {self.description}"


class Ingredient(Common):
    name = models.CharField(max_length=255, db_index=True)
    image = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Recipe(Common):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC"
        FRIENDS = "FRIENDS"
        PRIVATE = "PRIVATE"

    title = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
    )
    description = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    is_draft = models.BooleanField(default=True)

    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title or f"draft__{self.uid}"


class RecipeIngredient(Common):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"
