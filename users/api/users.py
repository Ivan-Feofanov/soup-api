import uuid

from django.core.exceptions import ValidationError
from ninja_extra import (
    api_controller,
    http_get,
    ControllerBase,
    http_patch,
    status,
)
from ninja_extra.exceptions import APIException, PermissionDenied
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth

from users.api.schemes import UserSchema, UserUpdateSchema


class ValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "something went wrong"


@api_controller("/users", tags=["users"], permissions=[IsAuthenticated], auth=JWTAuth())
class UserModelController(ControllerBase):
    @http_get("/me", response=UserSchema)
    def me(self, request):
        return request.user

    @http_patch("/{uuid:uid}", response=UserSchema)
    def update(self, request, uid: uuid.UUID, payload: UserUpdateSchema):
        user = request.user
        if user.uid != uid:
            raise PermissionDenied()
        for field, value in payload.model_dump().items():
            if value is not None:
                setattr(user, field, value)
        try:
            user.full_clean()
        except ValidationError as e:
            error_details = {
                "message": "Validation error occurred",
                "errors": e.message_dict,
            }
            raise ValidationException(detail=error_details)
        user.save()
        return user
