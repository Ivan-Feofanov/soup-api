from ninja import Router, Schema
from django.http import HttpRequest, QueryDict
from ninja_extra import status
from social_django.utils import load_strategy, load_backend
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.exceptions import TokenError, InvalidToken

from users.api.schemes import SocialAuthSchema, UserSchema, AuthResponseSchema


class TokenRefreshSchema(Schema):
    refresh: str


class TokenRefreshResponseSchema(Schema):
    access: str
    refresh: str


router = Router()


@router.post(
    "/login/{backend}/",
    response={
        status.HTTP_200_OK: AuthResponseSchema,
        status.HTTP_400_BAD_REQUEST: dict,
    },
)
def social_login(request: HttpRequest, backend: str, data: SocialAuthSchema):
    """
    Authenticates user via social network and returns JWT tokens.
    """
    post_data = QueryDict(mutable=True)
    post_data.update({"code": data.code, "redirect_uri": data.redirect_uri})
    request.POST = post_data
    strategy = load_strategy(request)
    backend = load_backend(strategy, "google-oauth2", redirect_uri=data.redirect_uri)
    try:
        user = backend.complete()

        if user and getattr(user, "is_active", False):
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            user_data = UserSchema.model_validate(user, from_attributes=True)
            return status.HTTP_200_OK, {
                "user": user_data,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }

        return status.HTTP_400_BAD_REQUEST, {
            "error": "Authentication failed or user is not active."
        }

    except Exception as e:
        print(f"Error during social login: {e}")
        return status.HTTP_400_BAD_REQUEST, {
            "error": "Invalid code or authentication error."
        }


@router.post("/logout/", response={status.HTTP_200_OK: dict})
def logout_view(request: HttpRequest):
    """
    Logout endpoint for JWT (client-side token removal).
    With JWT, logout is handled client-side by removing the tokens.
    This endpoint exists for API compatibility.
    """
    return status.HTTP_200_OK, {"success": True}


@router.post(
    "/token/refresh/",
    response={
        status.HTTP_200_OK: TokenRefreshResponseSchema,
        status.HTTP_400_BAD_REQUEST: dict,
    },
)
def refresh_token(request: HttpRequest, data: TokenRefreshSchema):
    """
    Refresh an access token using a refresh token.
    """
    try:
        refresh = RefreshToken(data.refresh)
        return status.HTTP_200_OK, {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    except (TokenError, InvalidToken) as e:
        return status.HTTP_400_BAD_REQUEST, {"error": str(e)}
