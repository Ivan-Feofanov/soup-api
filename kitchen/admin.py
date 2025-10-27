import logging
from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, Unit, Instruction

admin.site.register(Unit)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)

logger = logging.getLogger(__name__)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ["ingredient", "unit", "quantity", "notes"]


class InstructionInline(admin.StackedInline):
    model = Instruction
    extra = 1
    fields = ["step", "description", "timer"]
    readonly_fields = ["uid"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = ["visibility", "title", "description", "image", "notes", "author"]
    readonly_fields = ["uid"]
    inlines = [InstructionInline, RecipeIngredientInline]


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    fields = ["step", "description", "timer"]
    readonly_fields = ["uid"]
