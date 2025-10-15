from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from users.api.auth import router as auth_router
from kitchen.api import KitchenController
from users.api.users import UserModelController

api = NinjaExtraAPI()

api.register_controllers(NinjaJWTDefaultController)
api.register_controllers(UserModelController)
api.register_controllers(KitchenController)
api.add_router("/auth", auth_router)
