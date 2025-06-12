import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "centeral_server.settings")

# This will configure Django, load INSTALLED_APPS, etc.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
# Now it’s safe to import your routing, because apps are ready
import tunnel.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(tunnel.routing.websocket_urlpatterns),
})
