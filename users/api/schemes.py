from django.contrib.auth import get_user_model
from ninja import ModelSchema
from pydantic import BaseModel


UserModel = get_user_model()


class SocialAuthSchema(BaseModel):
    code: str
    redirect_uri: str


class UserSchema(ModelSchema):
    class Meta:
        model = UserModel
        fields = ["uid", "email", "handler", "username", "avatar"]


class UserUpdateSchema(BaseModel):
    handler: str | None = None
    username: str | None = None
    avatar: str | None = None


class AuthResponseSchema(BaseModel):
    user: UserSchema
