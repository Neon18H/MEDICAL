from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = scope.get("user", AnonymousUser())
        token = self._get_query_token(scope)
        if token:
            scope["user"] = await self._authenticate_token(token)
        return await self.inner(scope, receive, send)

    @staticmethod
    def _get_query_token(scope):
        query = parse_qs(scope.get("query_string", b"").decode())
        return query.get("token", [None])[0]

    @staticmethod
    async def _authenticate_token(token):
        authenticator = JWTAuthentication()
        try:
            validated = await sync_to_async(authenticator.get_validated_token)(token)
            return await sync_to_async(authenticator.get_user)(validated)
        except Exception:
            return AnonymousUser()


def JwtAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack

    return AuthMiddlewareStack(JwtAuthMiddleware(inner))
