from typing import Optional, Any
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser


class OptionalJWTAuth:
    """
    JWT authentication that allows anonymous users.
    If a valid token is provided, the user is authenticated.
    If no token or invalid token, request.user is AnonymousUser.

    This is used as auth=OptionalJWTAuth() in endpoints that should work
    for both authenticated and unauthenticated users.
    """

    def __call__(self, request: HttpRequest) -> Any:
        from ninja_jwt.authentication import JWTAuth

        # Get the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header or not auth_header.startswith('Bearer '):
            # No token provided, set anonymous user and return True to allow access
            request.user = AnonymousUser()
            return True

        try:
            # Try to authenticate with JWT
            jwt_auth = JWTAuth()
            result = jwt_auth(request)
            return result if result is not None else True
        except Exception:
            # If authentication fails, allow anonymous access
            request.user = AnonymousUser()
            return True

