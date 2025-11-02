import uuid

from django.db.models import Q
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
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

from kitchen.api.schemes import RecipeShortSchema, RecipeSchema, RecipeCreateSchema
from users.authentication import OptionalJWTAuth
from kitchen.models import Recipe, RecipeIngredient, Instruction


@api_controller("/kitchen/recipes", tags=["Recipes"])
class RecipesController(ControllerBase):
    @staticmethod
    def get_queryset(request):
        qs = (
            Recipe.objects.select_related("author")
            .prefetch_related(
                "instructions",
                "recipeingredient_set__ingredient",
                "recipeingredient_set__unit",
            )
            .filter(is_draft=False)
        )
        if request.user.is_authenticated:
            qs = qs.filter(Q(author=request.user) | Q(visibility="PUBLIC"))
        else:
            qs = qs.filter(visibility="PUBLIC")
        return qs.order_by("-updated_at")

    @http_get(
        "/",
        response=list[RecipeShortSchema],
        auth=OptionalJWTAuth(),
    )
    def list_recipes(self, request):
        return self.get_queryset(request)

    @http_get("/{uuid:uid}", response=RecipeSchema, auth=OptionalJWTAuth())
    def get_recipe(self, request, uid: uuid.UUID):
        return get_object_or_404(self.get_queryset(request), uid=uid)

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
        path="/{uuid:uid}",
        response={status.HTTP_204_NO_CONTENT: None},
        auth=JWTAuth(),
    )
    def delete_recipe(self, request, uid: uuid.UUID):
        recipe = get_object_or_404(Recipe, uid=uid)
        if recipe.author != request.user:
            raise PermissionDenied()
        recipe.delete()
        return status.HTTP_204_NO_CONTENT, None
