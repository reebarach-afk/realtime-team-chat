from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user(token):
    User = get_user_model()
    try:
        payload = AccessToken(token)  # validates signature + expiry
        return User.objects.get(id=payload["user_id"])
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Reads ?token=<access token> from the WebSocket URL and sets scope['user']."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]
        scope["user"] = await get_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
