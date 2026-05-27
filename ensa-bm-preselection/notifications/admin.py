# notifications/admin.py

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['destinataire', 'type_notif', 'sujet', 'statut', 'envoyee_le']
    list_filter   = ['statut', 'type_notif']
    search_fields = ['destinataire__email', 'sujet']
    readonly_fields = ['destinataire', 'sujet', 'contenu_html', 'envoyee_le', 'erreur']
    ordering      = ['-created_at']

    def has_add_permission(self, request): return False