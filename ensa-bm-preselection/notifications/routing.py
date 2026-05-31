# notifications/routing.py
# WebSocket URL patterns for notification progress tracking

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/notifications/(?P<task_id>[0-9a-f-]+)/$',
        consumers.NotificationProgressConsumer.as_asgi()
    ),
]
