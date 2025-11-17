from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden
from ninja_extra import NinjaExtraAPI

from kitchen.api.appliances.api import AppliancesController
from kitchen.api.ingredients import IngredientsController
from kitchen.api.recipes import RecipesController
from kitchen.api.drafts import RecipeDraftsController
from kitchen.api.units import UnitsController
from users.api.auth import router as auth_router
from users.api.users import UserModelController


def staff_or_secret_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        expected_token = settings.OPENAPI_GENERATOR_TOKEN
        incoming_token = request.headers.get("X-Ninja-Token")

        if settings.DEBUG:
            return view_func(request, *args, **kwargs)

        # Check token for generator
        if expected_token and incoming_token == expected_token:
            return view_func(request, *args, **kwargs)

        # Check staff for internal users
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden("Access denied")

    return _wrapped_view


api = NinjaExtraAPI(docs_decorator=staff_or_secret_required)

api.register_controllers(UserModelController)
api.register_controllers(RecipesController)
api.register_controllers(RecipeDraftsController)
api.register_controllers(IngredientsController)
api.register_controllers(UnitsController)
api.register_controllers(AppliancesController)

api.add_router("/auth", auth_router)
