"""
ASGI config for photo_client_site project.

It exposes the ASGI callable as a module-level variable named ``application``.
Normal pages go to Django as before; WebSocket connections (the chat) go to Channels.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
https://channels.readthedocs.io/en/latest/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_client_site.settings')

# Must run before importing anything that uses models (chat.routing does).
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # AuthMiddlewareStack gives the consumer the logged-in user from the session cookie.
    'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
})
