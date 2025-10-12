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
        fields = ["uid", "email", "first_name", "last_name"]


class AuthResponseSchema(BaseModel):
    access: str
    refresh: str
    user: UserSchema
