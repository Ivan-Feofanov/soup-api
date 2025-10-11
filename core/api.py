from ninja import NinjaAPI

api = NinjaAPI()

api.add_router("/kitchen", "kitchen.api.router")
