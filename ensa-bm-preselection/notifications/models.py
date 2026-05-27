# notifications/models.py

import uuid
from django.db import models
from users.models import User


class Notification(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        ENVOYEE    = 'ENVOYEE',    'Envoyée'
        ECHEC      = 'ECHEC',      'Échec d\'envoi'

    class TypeNotif(models.TextChoices):
        SOUMISSION    = 'SOUMISSION',    'Confirmation soumission'
        REJET_AUTO    = 'REJET_AUTO',    'Rejet automatique'
        REJET_MANUEL  = 'REJET_MANUEL',  'Rejet par responsable'
        PRESELECTION  = 'PRESELECTION',  'Présélection'
        INCOMPLET     = 'INCOMPLET',     'Dossier incomplet'
        COMPLEMENT    = 'COMPLEMENT',    'Demande de complément'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notif   = models.CharField(max_length=30, choices=TypeNotif.choices)
    sujet        = models.CharField(max_length=300)
    contenu_html = models.TextField()
    statut       = models.CharField(max_length=15, choices=Statut.choices, default=Statut.EN_ATTENTE)
    envoyee_le   = models.DateTimeField(null=True, blank=True)
    erreur       = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type_notif} → {self.destinataire.email} [{self.statut}]"