# scoring/admin.py

from django.contrib import admin
from .models import RegleRejet, ConfigScoring


@admin.register(RegleRejet)
class RegleRejetAdmin(admin.ModelAdmin):
    list_display  = ['filiere', 'type_regle', 'is_active', 'message_rejet_court']
    list_filter   = ['filiere', 'type_regle', 'is_active']
    list_editable = ['is_active']
    search_fields = ['filiere__nom', 'type_regle']

    def message_rejet_court(self, obj):
        return obj.message_rejet[:60] + "..." if len(obj.message_rejet) > 60 else obj.message_rejet
    message_rejet_court.short_description = "Message rejet"


@admin.register(ConfigScoring)
class ConfigScoringAdmin(admin.ModelAdmin):
    list_display  = ['filiere', 'matiere', 'poids', 'bonus_mention']
    list_filter   = ['filiere']
    search_fields = ['filiere__nom', 'matiere']
    ordering      = ['filiere', '-poids']