from django.contrib.auth import get_user_model
from ninja_extra import (
    ModelControllerBase,
    api_controller,
    ModelConfig,
    ModelSchemaConfig,
    http_get,
)
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth

from users.api.schemes import UserSchema


@api_controller("/users", tags=["users"], permissions=[IsAuthenticated], auth=JWTAuth())
class UserModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=get_user_model(),
        schema_config=ModelSchemaConfig(
            read_only_fields=["uid", "created_at"],
            include=["uid", "email", "first_name", "last_name", "created_at"],
            exclude=set(),
            depth=1,  # Nesting depth for related fields
        ),
        allowed_routes=["find_one", "update", "patch"],
    )

    @http_get("/me/", response=UserSchema)
    def me(self, request):
        return request.user
