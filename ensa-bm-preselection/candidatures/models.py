# candidatures/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Candidat
from administration.models import Filiere


def upload_document_path(instance, filename):
    # Les fichiers sont rangés par dossier : media/dossiers/{id}/{filename}
    return f"dossiers/{instance.dossier.id}/{filename}"


class Dossier(models.Model):

    class Statut(models.TextChoices):
        BROUILLON      = 'BROUILLON',      'Brouillon'
        EN_TRAITEMENT  = 'EN_TRAITEMENT',  'En traitement'
        INCOMPLET      = 'INCOMPLET',      'Incomplet'
        SUSPECT        = 'SUSPECT',        'Suspect (vérification manuelle)'
        REJETE_AUTO    = 'REJETE_AUTO',    'Rejeté automatiquement'
        EN_ATTENTE     = 'EN_ATTENTE',     'En attente de décision'
        PRESELECTIONNE = 'PRESELECTIONNE', 'Présélectionné'
        REJETE_FINAL   = 'REJETE_FINAL',   'Rejeté (décision finale)'

    class Mention(models.TextChoices):
        TRES_BIEN  = 'TB', 'Très Bien'
        BIEN       = 'B',  'Bien'
        ASSEZ_BIEN = 'AB', 'Assez Bien'
        PASSABLE   = 'P',  'Passable'

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidat            = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name='dossiers')
    filiere             = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='dossiers')
    statut              = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)

    # Informations académiques déclarées par le candidat
    diplome_obtenu      = models.CharField(max_length=200)
    etablissement_origine = models.CharField(max_length=300)
    annee_obtention     = models.PositiveIntegerField(null=True, blank=True)
    mention             = models.CharField(max_length=5, choices=Mention.choices, blank=True)
    moyenne_generale    = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                              validators=[MinValueValidator(0), MaxValueValidator(20)])

    # Calculé automatiquement par le moteur de scoring
    score               = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    classement          = models.PositiveIntegerField(null=True, blank=True)

    # Identifiants Massar / CNE
    code_massar         = models.CharField(max_length=20, blank=True,
                                           help_text="Code Massar du candidat")
    cne                 = models.CharField(max_length=20, blank=True,
                                           help_text="Code National de l'Étudiant")
    massar_verifie      = models.BooleanField(default=False,
                                              help_text="Vérification Massar confirmée manuellement")

    # Résultats de l'analyse automatique
    motif_rejet         = models.TextField(blank=True)
    score_confiance_ocr = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_suspect          = models.BooleanField(default=False)

    # Vérification d'authenticité des documents
    score_authenticite  = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        help_text="Score global d'authenticité des documents 0.0→1.0"
    )
    alertes_verification = models.JSONField(
        default=list, blank=True,
        help_text="Liste des alertes détectées lors de la vérification"
    )

    date_soumission     = models.DateTimeField(null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dossiers'
        verbose_name = 'Dossier'
        ordering = ['-score', 'created_at']

    def __str__(self):
        return f"Dossier {self.candidat.nom_complet} → {self.filiere.code} [{self.statut}]"

    def changer_statut(self, nouveau_statut, acteur=None, commentaire=''):
        from administration.models import HistoriqueAction
        from django.utils import timezone
        action_map = {
            self.Statut.BROUILLON: HistoriqueAction.TypeAction.MODIFICATION,
            self.Statut.EN_TRAITEMENT: HistoriqueAction.TypeAction.SOUMISSION,
            self.Statut.EN_ATTENTE: HistoriqueAction.TypeAction.SOUMISSION,
            self.Statut.INCOMPLET: HistoriqueAction.TypeAction.COMPLEMENT,
            self.Statut.SUSPECT: HistoriqueAction.TypeAction.MODIFICATION,
            self.Statut.REJETE_AUTO: HistoriqueAction.TypeAction.REJET_AUTO,
            self.Statut.PRESELECTIONNE: HistoriqueAction.TypeAction.PRESELECTION,
            self.Statut.REJETE_FINAL: HistoriqueAction.TypeAction.REJET_MANUEL,
        }
        ancien = self.statut
        self.statut = nouveau_statut
        if nouveau_statut == self.Statut.EN_TRAITEMENT and not self.date_soumission:
            self.date_soumission = timezone.now()
        self.save()
        HistoriqueAction.objects.create(
            dossier=self,
            acteur=acteur,
            action=action_map.get(nouveau_statut, HistoriqueAction.TypeAction.MODIFICATION),
            commentaire=commentaire or f"Statut changé de {ancien} vers {nouveau_statut}"
        )


class Document(models.Model):

    class TypeDocument(models.TextChoices):
        DIPLOME = 'DIPLOME', 'Diplôme'
        RELEVE  = 'RELEVE',  'Relevé de notes'
        CIN     = 'CIN',     'Carte d\'identité nationale'
        PHOTO   = 'PHOTO',   'Photo d\'identité'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dossier      = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='documents')
    type_doc     = models.CharField(max_length=20, choices=TypeDocument.choices)
    fichier      = models.FileField(upload_to=upload_document_path)
    taille_ko    = models.PositiveIntegerField(null=True, blank=True)
    mime_type    = models.CharField(max_length=100, blank=True)
    qualite_ocr  = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    date_upload  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents'
        verbose_name = 'Document'
        # Un seul document de chaque type par dossier
        unique_together = ['dossier', 'type_doc']

    def __str__(self):
        return f"{self.get_type_doc_display()} — {self.dossier}"

    def save(self, *args, **kwargs):
        # Calcul automatique de la taille à l'enregistrement
        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_ko = self.fichier.size // 1024
        super().save(*args, **kwargs)


class NoteMatiere(models.Model):

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dossier        = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='notes')
    matiere        = models.CharField(max_length=100)
    note_declaree  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(20)])
    note_extraite  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(20)])
    ecart          = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_suspect     = models.BooleanField(default=False)

    class Meta:
        db_table = 'notes_matieres'
        verbose_name = 'Note par Matière'
        unique_together = ['dossier', 'matiere']

    def __str__(self):
        return f"{self.matiere}: {self.note_declaree}/20 — {self.dossier}"

    def calculer_ecart(self):
        # Appelé après l'extraction OCR pour détecter les incohérences
        if self.note_declaree is not None and self.note_extraite is not None:
            self.ecart = abs(float(self.note_declaree) - float(self.note_extraite))
            self.is_suspect = self.ecart > 0.5
            self.save()
        return self.ecart
