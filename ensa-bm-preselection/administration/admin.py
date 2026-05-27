# administration/admin.py

from django.contrib import admin
from .models import Filiere, DiplomaAccepte, HistoriqueAction


class DiplomaAccepteInline(admin.TabularInline):
    # Affiche les diplômes directement dans la page filière
    model  = DiplomaAccepte
    extra  = 1
    fields = ['nom_diplome', 'etablissements', 'is_active']


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'code', 'niveau', 'places_disponibles', 'is_active', 'est_ouverte', 'candidatures_count']
    list_filter   = ['niveau', 'is_active']
    search_fields = ['nom', 'code']
    list_editable = ['is_active', 'places_disponibles']
    inlines       = [DiplomaAccepteInline]

    def est_ouverte(self, obj):
        return "✅ Ouverte" if obj.est_ouverte else "🔒 Fermée"
    est_ouverte.short_description = 'Statut'

    def candidatures_count(self, obj):
        return obj.candidatures_count
    candidatures_count.short_description = 'Candidatures'


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display  = ['dossier', 'action', 'acteur', 'timestamp', 'commentaire']
    list_filter   = ['action', 'timestamp']
    search_fields = ['dossier__candidat__nom', 'acteur__email']
    readonly_fields = ['dossier', 'acteur', 'action', 'timestamp']
    # L'historique ne doit jamais être modifié
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False