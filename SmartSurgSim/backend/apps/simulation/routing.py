from django.urls import re_path
from .consumers import AttemptConsumer

websocket_urlpatterns = [
    re_path(r'ws/attempts/(?P<attempt_id>\d+)/$', AttemptConsumer.as_asgi()),
]
