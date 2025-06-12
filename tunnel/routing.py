from django.urls import re_path
from .consumers import TunnelConsumer

websocket_urlpatterns = [
    re_path(r"ws/tunnel/$", TunnelConsumer.as_asgi()),
]
