# users/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import User, Candidat


class CandidatSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Candidat
        fields = ['id', 'nom', 'prenom', 'telephone', 'adresse', 'date_naissance', 'nom_complet']
        read_only_fields = ['id', 'nom_complet']


class UserSerializer(serializers.ModelSerializer):
    profil = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'email', 'cin', 'role', 'email_verified', 'created_at', 'profil']
        read_only_fields = ['id', 'role', 'email_verified', 'created_at']

    def get_profil(self, obj):
        try:
            return CandidatSerializer(obj.profil).data
        except Candidat.DoesNotExist:
            return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login par email — renvoie tokens + profil utilisateur."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        if self.username_field in attrs:
            attrs[self.username_field] = User.objects.normalize_email(
                attrs[self.username_field].strip()
            )
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class RegisterSerializer(serializers.Serializer):
    # Champs User
    email    = serializers.EmailField()
    cin      = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    # Champs Candidat
    nom            = serializers.CharField(max_length=100)
    prenom         = serializers.CharField(max_length=100)
    telephone      = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_naissance = serializers.DateField(required=False, allow_null=True)

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_cin(self, value):
        value = value.strip().upper()
        if User.objects.filter(cin__iexact=value).exists():
            raise serializers.ValidationError("Ce CIN est déjà enregistré.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        nom            = validated_data.pop('nom')
        prenom         = validated_data.pop('prenom')
        telephone      = validated_data.pop('telephone', '')
        date_naissance = validated_data.pop('date_naissance', None)

        user = User.objects.create_user(
            email    = validated_data['email'],
            cin      = validated_data['cin'],
            password = validated_data['password'],
            role     = User.Role.CANDIDAT,
        )
        Candidat.objects.create(
            user=user, nom=nom, prenom=prenom,
            telephone=telephone, date_naissance=date_naissance
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value
