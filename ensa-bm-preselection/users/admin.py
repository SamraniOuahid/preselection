# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Candidat


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'cin', 'role', 'is_active', 'email_verified', 'created_at']
    list_filter   = ['role', 'is_active', 'email_verified']
    search_fields = ['email', 'cin']
    ordering      = ['-created_at']
    # Colonnes cliquables pour changer rapidement
    list_editable = ['is_active']

    fieldsets = (
        ('Connexion',     {'fields': ('email', 'cin', 'password')}),
        ('Rôle & Statut', {'fields': ('role', 'is_active', 'is_staff', 'email_verified')}),
        ('Permissions',   {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'cin', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    list_display  = ['nom_complet', 'user__email', 'user__cin', 'telephone', 'date_naissance']
    search_fields = ['nom', 'prenom', 'user__email', 'user__cin']
    raw_id_fields = ['user']

    def user__email(self, obj):
        return obj.user.email
    user__email.short_description = 'Email'

    def user__cin(self, obj):
        return obj.user.cin
    user__cin.short_description = 'CIN'