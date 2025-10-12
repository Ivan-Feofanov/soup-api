from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from users.api.auth import router as auth_router
from kitchen.api import router as kitchen_router
from users.api.users import UserModelController

api = NinjaExtraAPI()

api.register_controllers(NinjaJWTDefaultController)
api.register_controllers(UserModelController)
api.add_router("/auth", auth_router)
api.add_router("/kitchen", kitchen_router)
