# chat/middleware.py
import urllib.parse
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        validated = AccessToken(token)
        user_id = validated.get("user_id") or validated.get("user")
        return User.objects.get(pk=user_id)
    except Exception:
        return AnonymousUser()

class JwtAuthMiddleware:
    """
    Custom middleware for JWT auth over WebSocket.
    Expects token in query string: ?token=<access_token>
    """
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JwtAuthMiddlewareInstance(scope, self.inner)

class JwtAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        query_string = self.scope.get("query_string", b"").decode()
        params = urllib.parse.parse_qs(query_string)
        token = params.get("token", [None])[0]
        if token:
            user = await get_user_from_token(token)
            self.scope["user"] = user
        else:
            self.scope["user"] = AnonymousUser()
        inner = self.inner(self.scope)
        return await inner(receive, send)
