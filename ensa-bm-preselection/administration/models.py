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
    date_ecrit         = models.DateTimeField(null=True, blank=True,
                           help_text="Date et heure de l'épreuve écrite")
    lieu_ecrit         = models.CharField(max_length=255, null=True, blank=True,
                           help_text="Lieu de l'épreuve écrite")
    # ── Informations épreuve orale ───────────────────────────────────
    date_oral          = models.DateTimeField(null=True, blank=True,
                           help_text="Date et heure de l'épreuve orale")
    lieu_oral          = models.CharField(max_length=255, null=True, blank=True,
                           help_text="Lieu de l'épreuve orale")
    coef_autre_diplome = models.DecimalField(max_digits=3, decimal_places=2, default=0.80,
                                             help_text="Coefficient appliqué aux diplômes 'Autre'")
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class DiplomaAccepte(models.Model):

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere         = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='diplomes_acceptes')
    nom_diplome     = models.CharField(max_length=200)  # ex: "DUT Informatique"
    coefficient     = models.DecimalField(max_digits=3, decimal_places=2, default=1.00,
                                         help_text="Coefficient multiplicateur pour le score du diplôme")
    # Liste des établissements acceptés, stockée en JSON
    # Si vide = tous les établissements sont acceptés
    etablissements  = models.JSONField(default=list, blank=True)
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'diplomes_acceptes'
        verbose_name = 'Diplôme Accepté'

    def __str__(self):
        return f"{self.nom_diplome} (coeff: {self.coefficient}) → {self.filiere.code}"


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


# ──────────────────────────────────────────────────────────────────
# EpreuveOrale — Gestion des épreuves orales
# ──────────────────────────────────────────────────────────────────

class EpreuveOrale(models.Model):
    """Épreuve orale pour une filière donnée."""

    class Statut(models.TextChoices):
        PLANIFIEE         = 'PLANIFIEE',         'Planifiée'
        EN_COURS          = 'EN_COURS',          'En cours'
        TERMINEE          = 'TERMINEE',          'Terminée'
        RESULTATS_PUBLIES = 'RESULTATS_PUBLIES', 'Résultats publiés'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filiere         = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='epreuves_oral')
    epreuve_ecrite  = models.ForeignKey(EpreuveEcrite, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='epreuves_oral',
                        help_text="Épreuve écrite liée")
    nom             = models.CharField(max_length=200,
                        help_text="Ex : Entretien oral — TDI Bac+2 — 2025")
    duree_minutes   = models.PositiveIntegerField(default=20,
                        help_text="Durée de chaque entretien en minutes")
    statut          = models.CharField(max_length=25, choices=Statut.choices,
                        default=Statut.PLANIFIEE)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                        null=True, related_name='epreuves_oral_creees')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'epreuves_orales'
        verbose_name = 'Épreuve Orale'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} [{self.get_statut_display()}]"

    @property
    def nb_convoques(self):
        return self.convocations.count()

    @property
    def nb_acceptes(self):
        return self.convocations.filter(decision='ACCEPTE').count()

    @property
    def nb_refuses(self):
        return self.convocations.filter(decision='REFUSE').count()

    @property
    def nb_absents(self):
        return self.convocations.filter(decision='ABSENT').count()

    @property
    def nb_en_attente(self):
        return self.convocations.filter(decision='EN_ATTENTE').count()


# ──────────────────────────────────────────────────────────────────
# ConvocationOrale — Convocation individuelle d'un candidat
# ──────────────────────────────────────────────────────────────────

class ConvocationOrale(models.Model):
    """Convocation d'un candidat à une épreuve orale."""

    class Decision(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente de décision'
        ACCEPTE    = 'ACCEPTE',    'Accepté'
        REFUSE     = 'REFUSE',     'Refusé'
        ABSENT     = 'ABSENT',     'Absent à l\'oral'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    epreuve_oral    = models.ForeignKey(EpreuveOrale, on_delete=models.CASCADE,
                        related_name='convocations')
    dossier         = models.ForeignKey('candidatures.Dossier', on_delete=models.CASCADE,
                        related_name='convocations_oral')

    # Créneau horaire assigné automatiquement
    heure_passage   = models.TimeField(null=True, blank=True,
                        help_text="Calculée automatiquement : heure_debut + (rang × duree_minutes)")
    numero_passage  = models.PositiveIntegerField(null=True,
                        help_text="Ordre de passage dans la journée")

    # Décision de l'oral
    decision        = models.CharField(max_length=15, choices=Decision.choices,
                        default=Decision.EN_ATTENTE)
    commentaire_jury = models.TextField(blank=True,
                        help_text="Note interne du jury (jamais visible au candidat)")
    date_decision   = models.DateTimeField(null=True, blank=True)
    decide_par      = models.ForeignKey(User, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='decisions_oral')

    # Documents requis vérifiés lors de l'oral
    bac_verifie          = models.BooleanField(default=False)
    diplome_verifie      = models.BooleanField(default=False)
    releve_notes_verifie = models.BooleanField(default=False)
    cin_verifie          = models.BooleanField(default=False)
    dossier_complet      = models.BooleanField(default=False)

    # Convocation générée
    convocation_generee = models.BooleanField(default=False)
    convocation_pdf     = models.FileField(upload_to='convocations/', null=True, blank=True)
    date_generation     = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'convocations_orales'
        verbose_name = 'Convocation Orale'
        unique_together = ['epreuve_oral', 'dossier']
        ordering = ['numero_passage']

    def __str__(self):
        return f"Convocation #{self.numero_passage} — {self.dossier} [{self.get_decision_display()}]"