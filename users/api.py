from django.contrib.auth import get_user_model
from ninja import Router, ModelSchema
from django.http import HttpRequest, QueryDict
from ninja_jwt.authentication import JWTAuth
from pydantic import BaseModel
from social_django.utils import load_strategy, load_backend

from ninja_jwt.tokens import RefreshToken

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


router = Router()


@router.post(
    "/login/{backend}/", response={200: AuthResponseSchema, 400: dict}
)  # Декоратор от social-django
def social_login(request: HttpRequest, backend: str, data: SocialAuthSchema):
    """
    Аутентифицирует пользователя через соц. сеть и возвращает JWT-токены.
    """
    post_data = QueryDict(mutable=True)
    post_data.update({"code": data.code, "redirect_uri": data.redirect_uri})
    request.POST = post_data
    strategy = load_strategy(request)
    # redirect_uri=None, так как фронтенд уже обработал редирект
    backend = load_backend(strategy, "google-oauth2", redirect_uri=data.redirect_uri)
    try:
        user = backend.complete()

        if user and getattr(user, "is_active", False):
            refresh = RefreshToken.for_user(user)
            tokens = {"access": str(refresh.access_token), "refresh": str(refresh)}
            user_data = UserSchema.model_validate(user, from_attributes=True)
            return 200, {"user": user_data, **tokens}

        return 400, {"error": "Authentication failed or user is not active."}

    except Exception as e:
        print(f"Error during social login: {e}")
        return 400, {"error": "Invalid code or authentication error."}


@router.get("/me/", response=UserSchema, auth=JWTAuth())
def me(request):
    return request.user
