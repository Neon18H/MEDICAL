import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Attempt, Event


class AttemptConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.attempt_id = self.scope['url_route']['kwargs']['attempt_id']
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return
        allowed = await self._user_owns_attempt(user.id, self.attempt_id)
        if not allowed:
            await self.close()
            return
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        payload = json.loads(text_data)
        event = await self._save_event(payload)
        if event:
            await self.send(text_data=json.dumps({'type': 'ack', 'event_id': event.id}))
            if payload.get('type') == 'hit' and payload.get('payload', {}).get('zone') == 'prohibited':
                await self.send(text_data=json.dumps({'type': 'warning', 'message': 'Entering prohibited zone'}))

    @database_sync_to_async
    def _user_owns_attempt(self, user_id, attempt_id):
        return Attempt.objects.filter(id=attempt_id, user_id=user_id).exists()

    @database_sync_to_async
    def _save_event(self, payload):
        attempt = Attempt.objects.filter(id=self.attempt_id).first()
        if not attempt:
            return None
        return Event.objects.create(
            attempt=attempt,
            t_ms=payload.get('t_ms', 0),
            event_type=payload.get('type', 'unknown'),
            payload=payload.get('payload', {}),
        )
