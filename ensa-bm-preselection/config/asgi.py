"""
ASGI config for config project.

Routes HTTP traffic to Django and WebSocket traffic
to Channels consumers via ProtocolTypeRouter.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django ASGI app must be initialized BEFORE importing routing
django_asgi_app = get_asgi_application()

import notifications.routing  # noqa: E402 — must be after django setup

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(notifications.routing.websocket_urlpatterns)
        )
    ),
})
