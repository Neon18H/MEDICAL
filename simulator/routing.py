from django.urls import path

from .consumers import AttemptConsumer

websocket_urlpatterns = [
    path("ws/attempts/<int:attempt_id>/", AttemptConsumer.as_asgi()),
]
