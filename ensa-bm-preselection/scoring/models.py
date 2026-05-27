# scoring/models.py

import uuid
from django.db import models
from administration.models import Filiere


class RegleRejet(models.Model):

    class TypeRegle(models.TextChoices):
        DIPLOME_INVALIDE      = 'DIPLOME_INVALIDE',      'Diplôme non accepté'
        MOYENNE_INSUFFISANTE  = 'MOYENNE_INSUFFISANTE',  'Moyenne générale insuffisante'
        NOTE_ELIMINATOIRE     = 'NOTE_ELIMINATOIRE',     'Note éliminatoire dans une matière'
        ETABLISSEMENT_INVALIDE = 'ETABLISSEMENT_INVALIDE', 'Établissement non reconnu'
        DOUBLON_CIN           = 'DOUBLON_CIN',           'Doublon CIN détecté'
        DATE_INCOHERENTE      = 'DATE_INCOHERENTE',      'Incohérence date diplôme'
        DOCUMENT_MANQUANT     = 'DOCUMENT_MANQUANT',     'Document obligatoire manquant'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere        = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='regles')
    type_regle     = models.CharField(max_length=50, choices=TypeRegle.choices)
    is_active      = models.BooleanField(default=True)
    message_rejet  = models.TextField()  # Message affiché au candidat si rejeté
    # Paramètres flexibles selon le type de règle, exemples :
    # MOYENNE_INSUFFISANTE → {"seuil": 12.0}
    # NOTE_ELIMINATOIRE   → {"matiere": "Mathématiques", "seuil": 8.0}
    # DIPLOME_INVALIDE    → (pas de paramètre, utilise DiplomaAccepte)
    parametre      = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'regles_rejet'
        verbose_name = 'Règle de Rejet'
        unique_together = ['filiere', 'type_regle']

    def __str__(self):
        statut = "✓" if self.is_active else "✗"
        return f"[{statut}] {self.get_type_regle_display()} — {self.filiere.code}"


class ConfigScoring(models.Model):

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='config_scoring')
    matiere = models.CharField(max_length=100)
    poids   = models.DecimalField(max_digits=5, decimal_places=2)
    # Bonus selon la mention obtenue au diplôme
    # Exemple : {"TB": 2.0, "B": 1.0, "AB": 0.5, "P": 0.0}
    bonus_mention = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'config_scoring'
        verbose_name = 'Configuration Scoring'
        unique_together = ['filiere', 'matiere']

    def __str__(self):
        return f"{self.filiere.code} — {self.matiere} ({self.poids}%)"