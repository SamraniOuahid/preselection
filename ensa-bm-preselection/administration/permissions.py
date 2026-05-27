# administration/permissions.py

from rest_framework.permissions import BasePermission
from users.models import User


class IsResponsableOrAdmin(BasePermission):
    """Seuls les responsables et admins peuvent accéder."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [User.Role.RESPONSABLE, User.Role.ADMIN]
        )


class IsAdminOnly(BasePermission):
    """Réservé aux administrateurs uniquement."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN