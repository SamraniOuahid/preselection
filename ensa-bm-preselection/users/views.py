# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from .models import User, Candidat
from .serializers import (
    RegisterSerializer, UserSerializer, CandidatSerializer,
    ChangePasswordSerializer, CustomTokenObtainPairSerializer,
    VerifyEmailConfirmSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
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
        
        # Generer token et envoyer email de vérification
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # Assurez-vous que l'URL front-end est configurée, ex: settings.FRONTEND_URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verify_link = f"{frontend_url}/verify-email?uid={uid}&token={token}"
        
        subject = "Confirmation de votre compte - ENSA Béni Mellal"
        message = f"Bonjour,\n\nVeuillez cliquer sur le lien suivant pour confirmer votre compte :\n{verify_link}\n\nCordialement,\nL'équipe ENSA BM"
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            # En environnement dev, si l'email n'est pas bien configuré, on l'affiche au moins en console ou on ignore.
            pass

        return Response({
            "message": "Compte créé avec succès. Un e-mail de confirmation vous a été envoyé.",
            "user": UserSerializer(user).data
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


class VerifyEmailConfirmView(APIView):
    """
    POST /api/auth/verify-email-confirm/
    Valide l'uid et le token pour activer le compte
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            return Response({"message": "Votre compte a été vérifié avec succès. Vous pouvez maintenant vous connecter."}, status=status.HTTP_200_OK)
        return Response({"error": "Le lien de vérification est invalide ou a expiré."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    POST /api/auth/password-reset/
    Génère un token de réinitialisation et l'envoie par email
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Sécurité : ne pas révéler que l'email n'existe pas
            return Response({"message": "Si l'adresse email existe, un lien de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)
            
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"
        
        subject = "Réinitialisation de votre mot de passe - ENSA Béni Mellal"
        message = f"Bonjour,\n\nVous avez demandé la réinitialisation de votre mot de passe. Veuillez cliquer sur le lien suivant pour choisir un nouveau mot de passe :\n{reset_link}\n\nSi vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.\n\nCordialement,\nL'équipe ENSA BM"
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception:
            pass

        return Response({"message": "Si l'adresse email existe, un lien de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset-confirm/
    Vérifie l'uid et le token, et met à jour le mot de passe
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.email_verified = True  # Valider l'email car l'utilisateur a prouvé qu'il y a accès
            user.save()
            return Response({"message": "Votre mot de passe a été réinitialisé avec succès."}, status=status.HTTP_200_OK)
        return Response({"error": "Le lien de réinitialisation est invalide ou a expiré."}, status=status.HTTP_400_BAD_REQUEST)

