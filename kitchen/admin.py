from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField

from .models import Ingredient, Recipe, RecipeIngredient, Unit

admin.site.register(Unit)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)


class RecipeForm(forms.ModelForm):
    instructions = SimpleArrayField(
        forms.CharField(),
        widget=forms.Textarea,
        delimiter="|",
    )

    class Meta:
        model = Recipe
        fields = "__all__"


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ["ingredient", "unit", "quantity", "notes"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeForm
    fields = ["name", "description", "image", "notes", "instructions", "author"]
    readonly_fields = ["uid"]
    inlines = [RecipeIngredientInline]
