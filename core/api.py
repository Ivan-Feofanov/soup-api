from ninja_extra import NinjaExtraAPI

from kitchen.api.ingredients import IngredientsController
from kitchen.api.recipes import RecipesController, RecipeDraftsController
from kitchen.api.units import UnitsController
from users.api.auth import router as auth_router
from users.api.users import UserModelController

api = NinjaExtraAPI()

api.register_controllers(UserModelController)
api.register_controllers(RecipesController)
api.register_controllers(RecipeDraftsController)
api.register_controllers(IngredientsController)
api.register_controllers(UnitsController)

api.add_router("/auth", auth_router)
