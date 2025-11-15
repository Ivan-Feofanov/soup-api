from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema
from pydantic import BaseModel

from shared.schemes import UIDSchema

UserModel = get_user_model()


class SocialAuthSchema(BaseModel):
    code: str
    redirect_uri: str


class UserSchema(UIDSchema, ModelSchema):
    class Meta:
        model = UserModel
        fields = ["email", "handler", "username", "avatar"]


class UserUpdateSchema(BaseModel):
    handler: str | None = None
    username: str | None = None
    avatar: str | None = None


class AuthResponseSchema(BaseModel):
    user: UserSchema
    access_token: str
    refresh_token: str


class TokenRefreshResponseSchema(Schema):
    access_token: str
    refresh_token: str


class TokenRefreshSchema(Schema):
    refresh_token: str
