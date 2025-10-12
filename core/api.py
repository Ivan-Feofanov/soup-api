from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from users.api import router as users_router
from kitchen.api import router as kitchen_router

api = NinjaExtraAPI()

api.register_controllers(NinjaJWTDefaultController)
api.add_router("/auth", users_router)
api.add_router("/kitchen", kitchen_router)
