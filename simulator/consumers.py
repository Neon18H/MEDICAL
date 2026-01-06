import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Attempt, Event

User = get_user_model()


class AttemptConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.attempt_id = self.scope["url_route"]["kwargs"]["attempt_id"]
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            self.user = await self._authenticate_query_token()
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        if not await self._can_access_attempt(self.attempt_id, self.user):
            await self.close(code=4403)
            return
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        payload = json.loads(text_data)
        event_type = payload.get("event_type")
        timestamp_ms = payload.get("timestamp_ms", 0)
        data = payload.get("payload", {})
        await self._create_event(self.attempt_id, event_type, data, timestamp_ms)
        await self.send(text_data=json.dumps({"status": "ok"}))

    async def _create_event(self, attempt_id, event_type, data, timestamp_ms):
        await sync_to_async(Event.objects.create)(
            attempt_id=attempt_id,
            event_type=event_type,
            payload=data,
            timestamp_ms=timestamp_ms,
        )

    async def _can_access_attempt(self, attempt_id, user):
        attempt = await sync_to_async(Attempt.objects.select_related("user").get)(id=attempt_id)
        if user.role in {"INSTRUCTOR", "ADMIN"}:
            return True
        return attempt.user_id == user.id

    async def _authenticate_query_token(self):
        query = parse_qs(self.scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]
        if not token:
            return None
        return await sync_to_async(self._get_user_from_token)(token)

    def _get_user_from_token(self, token: str):
        authenticator = JWTAuthentication()
        validated = authenticator.get_validated_token(token)
        return authenticator.get_user(validated)
