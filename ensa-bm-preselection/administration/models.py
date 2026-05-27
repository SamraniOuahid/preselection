# administration/models.py

import uuid
from django.db import models
from users.models import User


class Filiere(models.Model):

    class Niveau(models.TextChoices):
        BAC2 = 'BAC2', 'Bac+2'
        BAC3 = 'BAC3', 'Bac+3'

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom                = models.CharField(max_length=200)
    code               = models.CharField(max_length=20, unique=True)  # ex: "GI-BAC2"
    niveau             = models.CharField(max_length=10, choices=Niveau.choices)
    description        = models.TextField(blank=True)
    places_disponibles = models.PositiveIntegerField(default=30)
    is_active          = models.BooleanField(default=True)
    date_ouverture     = models.DateTimeField(null=True, blank=True)
    date_fermeture     = models.DateTimeField(null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'filieres'
        verbose_name = 'Filière'
        ordering = ['niveau', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.niveau})"

    @property
    def est_ouverte(self):
        from django.utils import timezone
        now = timezone.now()
        if self.date_ouverture and self.date_fermeture:
            return self.date_ouverture <= now <= self.date_fermeture
        return self.is_active

    @property
    def candidatures_count(self):
        return self.dossiers.count()


class DiplomaAccepte(models.Model):

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere         = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='diplomes_acceptes')
    nom_diplome     = models.CharField(max_length=200)  # ex: "DUT Informatique"
    # Liste des établissements acceptés, stockée en JSON
    # Si vide = tous les établissements sont acceptés
    etablissements  = models.JSONField(default=list, blank=True)
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'diplomes_acceptes'
        verbose_name = 'Diplôme Accepté'

    def __str__(self):
        return f"{self.nom_diplome} → {self.filiere.code}"


class HistoriqueAction(models.Model):

    class TypeAction(models.TextChoices):
        SOUMISSION       = 'SOUMISSION',       'Soumission dossier'
        VALIDATION       = 'VALIDATION',       'Validation responsable'
        REJET_AUTO       = 'REJET_AUTO',       'Rejet automatique'
        REJET_MANUEL     = 'REJET_MANUEL',     'Rejet manuel'
        PRESELECTION     = 'PRESELECTION',     'Présélection'
        COMPLEMENT       = 'COMPLEMENT',       'Demande complément'
        MODIFICATION     = 'MODIFICATION',     'Modification dossier'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # dossier est importé ici pour éviter les imports circulaires
    dossier     = models.ForeignKey('candidatures.Dossier', on_delete=models.CASCADE, related_name='historique')
    acteur      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions')
    action      = models.CharField(max_length=50, choices=TypeAction.choices)
    commentaire = models.TextField(blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historique_actions'
        verbose_name = 'Action'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} — {self.timestamp.strftime('%d/%m/%Y %H:%M')}"