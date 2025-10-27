from django.contrib.auth import login, logout
from ninja import Router
from django.http import HttpRequest, QueryDict
from social_django.utils import load_strategy, load_backend

from users.api.schemes import SocialAuthSchema, UserSchema, AuthResponseSchema

router = Router()


@router.post(
    "/login/{backend}/", response={200: AuthResponseSchema, 400: dict}
)
def social_login(request: HttpRequest, backend: str, data: SocialAuthSchema):
    """
    Authenticates user via social network and creates a session.
    """
    post_data = QueryDict(mutable=True)
    post_data.update({"code": data.code, "redirect_uri": data.redirect_uri})
    request.POST = post_data
    strategy = load_strategy(request)
    backend = load_backend(strategy, "google-oauth2", redirect_uri=data.redirect_uri)
    try:
        user = backend.complete()

        if user and getattr(user, "is_active", False):
            login(request, user)
            request.session.save()
            user_data = UserSchema.model_validate(user, from_attributes=True)
            return 200, {"user": user_data}

        return 400, {"error": "Authentication failed or user is not active."}

    except Exception as e:
        print(f"Error during social login: {e}")
        return 400, {"error": "Invalid code or authentication error."}


@router.post("/logout/", response={200: dict})
def logout_view(request: HttpRequest):
    """
    Logs out the user and destroys the session.
    """
    logout(request)
    return 200, {"success": True}
