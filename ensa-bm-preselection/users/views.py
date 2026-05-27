# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Candidat
from .serializers import (
    RegisterSerializer, UserSerializer, CandidatSerializer,
    ChangePasswordSerializer, CustomTokenObtainPairSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Réponse: { access, refresh, user }
    """
    permission_classes = [permissions.AllowAny]
    serializer_class   = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Crée un compte candidat + profil en une seule requête.
    Accessible sans authentification.
    """
    serializer_class    = RegisterSerializer
    permission_classes  = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Générer les tokens JWT directement après l'inscription
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Compte créé avec succès.",
            "user": UserSerializer(user).data,
            "tokens": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/  → Retourne le profil de l'utilisateur connecté
    PUT  /api/auth/me/  → Met à jour le profil candidat
    """
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        from .models import Candidat
        try:
            candidat = request.user.profil
        except Candidat.DoesNotExist:
            return Response(
                {"error": "Seuls les candidats peuvent modifier leur profil."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CandidatSerializer(candidat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({"message": "Mot de passe modifié avec succès."})


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blackliste le refresh token pour invalider la session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token manquant."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"error": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Déconnexion réussie."})
