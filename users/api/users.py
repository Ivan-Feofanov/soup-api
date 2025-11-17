import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ninja_extra import (
    api_controller,
    http_get,
    ControllerBase,
    http_patch,
    status,
)
from ninja_extra.exceptions import APIException, PermissionDenied
from ninja_jwt.authentication import JWTAuth

from users.api.schemes import UserSchema, UserUpdateSchema

user_model = get_user_model()


class ValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "something went wrong"


@api_controller("/users", tags=["users"], auth=JWTAuth())
class UserModelController(ControllerBase):
    @http_get("/me", response=UserSchema)
    def me(self, request):
        return request.user

    @http_patch("/{uuid:uid}", response=UserSchema)
    def update(self, request, uid: uuid.UUID, payload: UserUpdateSchema):
        user = request.user
        if user.uid != uid:
            raise PermissionDenied()
        if payload.handler:
            payload.handler = payload.handler.lower().strip()
            if (
                user_model.objects.filter(handler__iexact=payload.handler)
                .exclude(uid=user.uid)
                .exists()
            ):
                raise ValidationException(
                    detail={
                        "errors": {
                            "handler": [
                                "This handler is already taken by another chief."
                            ]
                        }
                    }
                )
        user.username = payload.username
        user.handler = user.handler or payload.handler
        user.avatar = payload.avatar
        user.save()
        return user
