import uuid

from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from ninja_extra import (
    api_controller,
    ControllerBase,
    http_get,
    http_post,
    status,
    http_patch,
    http_delete,
)
from ninja_jwt.authentication import JWTAuth

from kitchen.api.schemes import RecipeSchema, DraftSchema
from kitchen.models import Recipe, RecipeIngredient, Instruction
from users.api.users import ValidationException
from users.authentication import OptionalJWTAuth


@api_controller("/kitchen/recipes/drafts", tags=["RecipeDrafts"], auth=JWTAuth())
class RecipeDraftsController(ControllerBase):
    @staticmethod
    def get_queryset(request):
        if not request.user.is_authenticated:
            return Recipe.objects.none()
        return (
            Recipe.objects.select_related("author")
            .prefetch_related(
                "instructions",
                "recipeingredient_set__ingredient",
                "recipeingredient_set__unit",
            )
            .filter(is_draft=True, author=request.user)
        )

    @http_get(
        "/",
        response=list[RecipeSchema],
    )
    def list_drafts(self, request):
        return self.get_queryset(request)

    @http_get("/{uuid:uid}", response=RecipeSchema, auth=OptionalJWTAuth())
    def get_draft(self, request, uid: uuid.UUID):
        return get_object_or_404(self.get_queryset(request), uid=uid)

    @http_post(
        "/",
        response={
            status.HTTP_200_OK: RecipeSchema,
            status.HTTP_201_CREATED: RecipeSchema,
            status.HTTP_400_BAD_REQUEST: dict,
        },
    )
    def create_draft(self, request):
        if self.get_queryset(request).exists():
            return self.get_queryset(request).first()
        recipe = Recipe.objects.create(author=request.user)
        return status.HTTP_201_CREATED, recipe

    @http_patch(
        "/{uuid:uid}",
        response=RecipeSchema,
    )
    def update_draft(self, request, uid: uuid.UUID, payload: DraftSchema):
        with atomic():
            recipe = get_object_or_404(self.get_queryset(request), uid=uid)
            recipe_payload = payload.model_dump()
            del recipe_payload["ingredients"]
            if payload.ingredients:
                recipe.recipeingredient_set.all().delete()
                for ingredient in payload.ingredients:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient_id=ingredient.ingredient_uid,
                        unit_id=ingredient.unit_uid,
                        quantity=ingredient.quantity,
                    )
            del recipe_payload["instructions"]
            if payload.instructions:
                recipe.instructions.all().delete()
                for instruction in payload.instructions:
                    if instruction.description.strip():
                        Instruction.objects.create(
                            recipe=recipe,
                            step=instruction.step,
                            description=instruction.description,
                            timer=instruction.timer,
                        )
            for field, value in recipe_payload.items():
                if value is not None:
                    setattr(recipe, field, value)
            recipe.save()
            recipe.refresh_from_db()
            return recipe

    @http_delete(
        path="/{uuid:uid}",
        response={status.HTTP_204_NO_CONTENT: None},
    )
    def delete_draft(self, request, uid: uuid.UUID):
        recipe = get_object_or_404(self.get_queryset(request), uid=uid)
        recipe.delete()
        return status.HTTP_204_NO_CONTENT, None

    @http_post(
        path="/{uuid:uid}/finish",
        response={status.HTTP_200_OK: None},
    )
    def finish_draft(self, request, uid: uuid.UUID):
        recipe = get_object_or_404(self.get_queryset(request), uid=uid)

        # Validate that the recipe is complete
        errors = {}
        if recipe.instructions.count() == 0:
            errors["instructions"] = ["Instructions are required"]
        if recipe.recipeingredient_set.count() == 0:
            errors["ingredients"] = ["Ingredients are required"]
        if not recipe.description:
            errors["description"] = ["Description is required"]
        if errors:
            raise ValidationException(detail={"errors": errors})

        recipe.is_draft = False
        recipe.save()
        return status.HTTP_200_OK, None
