import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Attempt, Event

User = get_user_model()


class AttemptConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.attempt_id = self.scope["url_route"]["kwargs"]["attempt_id"]
        self.user = self.scope.get("user")
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
        response = {"status": "ok"}
        if event_type == "hit" and data.get("zone") == "forbidden":
            response["warning"] = "Estás en una zona prohibida. Ajusta la trayectoria."
        if event_type == "action" and data.get("type"):
            response["hint"] = f"Verifica la técnica para {data.get('type').lower()}."
        await self.send(text_data=json.dumps(response))

    async def _create_event(self, attempt_id, event_type, data, timestamp_ms):
        await sync_to_async(Event.objects.create)(
            attempt_id=attempt_id,
            event_type=event_type,
            payload=data,
            timestamp_ms=timestamp_ms,
        )

    async def _can_access_attempt(self, attempt_id, user):
        try:
            attempt = await sync_to_async(Attempt.objects.select_related("user").get)(id=attempt_id)
        except Attempt.DoesNotExist:
            return False
        if user.role in {"INSTRUCTOR", "ADMIN"}:
            return True
        return attempt.user_id == user.id
