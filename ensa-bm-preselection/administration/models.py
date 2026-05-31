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
    # ── Informations épreuve écrite ──────────────────────────────────
    date_ecrit         = models.DateField(null=True, blank=True,
                           help_text="Date de l'épreuve écrite")
    heure_ecrit        = models.CharField(max_length=50, null=True, blank=True,
                           help_text="Heure de l'épreuve écrite (ex: 09:00)")
    lieu_ecrit         = models.CharField(max_length=255, null=True, blank=True,
                           help_text="Lieu de l'épreuve écrite")
    # ── Informations épreuve orale ───────────────────────────────────
    date_oral          = models.DateField(null=True, blank=True,
                           help_text="Date de l'épreuve orale")
    heure_oral         = models.CharField(max_length=50, null=True, blank=True,
                           help_text="Heure de l'épreuve orale (ex: 09:00)")
    lieu_oral          = models.CharField(max_length=255, null=True, blank=True,
                           help_text="Lieu de l'épreuve orale")
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
    dossier     = models.ForeignKey('candidatures.Dossier', on_delete=models.CASCADE,
                    null=True, blank=True, related_name='historique')
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


class EpreuveEcrite(models.Model):
    """Épreuve écrite pour une filière donnée."""

    class Statut(models.TextChoices):
        NON_COMMENCEE     = 'NON_COMMENCEE',     'Non commencée'
        EN_COURS          = 'EN_COURS',           'En cours'
        NOTES_IMPORTEES   = 'NOTES_IMPORTEES',    'Notes importées'
        RESULTATS_PUBLIES = 'RESULTATS_PUBLIES',  'Résultats publiés'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere         = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='epreuves')
    nom             = models.CharField(max_length=200,
                        help_text="Ex : Épreuve écrite — GIR Bac+2 — Session 2025")
    date_epreuve    = models.DateField(null=True, blank=True)
    date_oral       = models.DateField(null=True, blank=True,
                        help_text="Date de l'épreuve orale")
    lieu_oral       = models.CharField(max_length=255, null=True, blank=True,
                        help_text="Lieu de l'épreuve orale")
    heure_oral      = models.CharField(max_length=50, null=True, blank=True,
                        help_text="Heure de l'épreuve orale")
    seuil_admission = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                        help_text="Note minimale pour être admis")
    note_sur        = models.DecimalField(max_digits=5, decimal_places=2, default=20.00,
                        help_text="Barème de l'épreuve (20, 40, 100...)")
    coefficient     = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                        help_text="Coefficient dans le score final")
    statut          = models.CharField(max_length=20, choices=Statut.choices,
                        default=Statut.NON_COMMENCEE)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                        null=True, related_name='epreuves_creees')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'epreuves_ecrites'
        verbose_name = 'Épreuve Écrite'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} [{self.get_statut_display()}]"

    @property
    def nb_admis(self):
        return self.notes.filter(note__gte=self.seuil_admission).count()

    @property
    def nb_recales(self):
        return self.notes.filter(note__lt=self.seuil_admission).count()

    @property
    def nb_absents(self):
        return self.notes.filter(note__isnull=True).count()

    @property
    def moyenne_promo(self):
        from django.db.models import Avg
        result = self.notes.filter(note__isnull=False).aggregate(Avg('note'))
        return result['note__avg']


class NoteEcrite(models.Model):
    """Note individuelle d'un candidat à une épreuve écrite."""

    class Resultat(models.TextChoices):
        ADMIS  = 'ADMIS',  'Admis'
        RECALE = 'RECALE', 'Recalé'
        ABSENT = 'ABSENT', 'Absent'
        ANNULE = 'ANNULE', 'Note annulée'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    epreuve          = models.ForeignKey(EpreuveEcrite, on_delete=models.CASCADE,
                         related_name='notes')
    dossier          = models.ForeignKey('candidatures.Dossier', on_delete=models.CASCADE,
                         related_name='notes_ecrits')
    note             = models.DecimalField(max_digits=5, decimal_places=2,
                         null=True, blank=True)
    resultat         = models.CharField(max_length=10, choices=Resultat.choices, blank=True)
    rang_final       = models.PositiveIntegerField(null=True, blank=True)
    note_importee_le = models.DateTimeField(null=True, blank=True)

    # Champs de traçabilité import Excel
    ligne_excel      = models.PositiveIntegerField(null=True, blank=True,
                         help_text="Numéro de ligne dans le fichier Excel source")
    import_hash      = models.CharField(max_length=64, blank=True,
                         help_text="Hash MD5 du fichier Excel importé")

    class Meta:
        db_table = 'notes_ecrites'
        verbose_name = 'Note Écrite'
        unique_together = ['epreuve', 'dossier']
        ordering = ['-note']

    def __str__(self):
        return f"Note {self.note}/{self.epreuve.note_sur} — {self.dossier}"

    def calculer_resultat(self):
        """Met à jour le champ resultat selon le seuil d'admission."""
        if self.note is None:
            self.resultat = self.Resultat.ABSENT
        elif self.note >= self.epreuve.seuil_admission:
            self.resultat = self.Resultat.ADMIS
        else:
            self.resultat = self.Resultat.RECALE
        self.save()