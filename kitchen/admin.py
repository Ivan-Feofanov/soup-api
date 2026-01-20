import logging

from django.contrib import admin

from .models import (
    Appliance,
    ApplianceType,
    Ingredient,
    Instruction,
    Manufacturer,
    Recipe,
    RecipeIngredient,
    Unit,
)

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


class ApplianceInline(admin.TabularInline):
    model = Recipe.appliances.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = ["visibility", "title", "description", "image", "notes", "author"]
    readonly_fields = ["uid"]
    inlines = [InstructionInline, RecipeIngredientInline, ApplianceInline]


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    fields = ["step", "description", "timer"]
    readonly_fields = ["uid"]


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    fields = ["model", "manufacturer", "type"]
    readonly_fields = ["uid"]


@admin.register(ApplianceType)
class ApplianceTypeAdmin(admin.ModelAdmin):
    fields = ["name"]
    readonly_fields = ["uid"]


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    fields = ["name"]
    readonly_fields = ["uid"]
