# users/models.py

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ─────────────────────────────────────────────────────────────────
# Manager personnalisé — explique à Django comment créer un User
# ─────────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):

    def create_user(self, email, cin, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        if not cin:
            raise ValueError("Le CIN est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, cin=cin, **extra_fields)
        user.set_password(password)  # hash automatique
        user.save(using=self._db)
        return user

    def create_superuser(self, email, cin, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, cin, password, **extra_fields)


# ─────────────────────────────────────────────────────────────────
# Modèle User — remplace le User Django par défaut
# ─────────────────────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CANDIDAT    = 'CANDIDAT',    'Candidat'
        RESPONSABLE = 'RESPONSABLE', 'Responsable Scolarité'
        ADMIN       = 'ADMIN',       'Administrateur'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email          = models.EmailField(unique=True)
    cin            = models.CharField(max_length=20, unique=True)
    role           = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDAT)
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Django utilise ce champ comme identifiant de connexion (au lieu de username)
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['cin']

    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'

    def __str__(self):
        return f"{self.email} ({self.role})"

    # Propriétés utiles dans les vues
    @property
    def is_candidat(self):
        return self.role == self.Role.CANDIDAT

    @property
    def is_responsable(self):
        return self.role == self.Role.RESPONSABLE

    @property
    def profil_id(self):
        profil = getattr(self, 'profil', None)
        return profil.id if profil else None


# ─────────────────────────────────────────────────────────────────
# Modèle Candidat — informations personnelles du candidat
# ─────────────────────────────────────────────────────────────────
class Candidat(models.Model):

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    nom            = models.CharField(max_length=100)
    prenom         = models.CharField(max_length=100)
    telephone      = models.CharField(max_length=20, blank=True)
    adresse        = models.TextField(blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'candidats'
        verbose_name = 'Candidat'

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"