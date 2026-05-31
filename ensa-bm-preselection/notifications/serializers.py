# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = [
            'id', 'type_notif', 'sujet',
            'contenu_html', 'envoyee_le', 'lue', 'lue_le'
        ]
