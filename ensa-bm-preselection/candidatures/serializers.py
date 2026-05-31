# candidatures/serializers.py

from rest_framework import serializers
from .models import Dossier, Document, NoteMatiere
from users.serializers import CandidatSerializer
from users.models import Candidat
from administration.models import Filiere


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NoteMatiere
        fields = [
            'id', 'matiere', 'note_declaree', 'note_extraite',
            'ecart', 'is_suspect',
        ]
        read_only_fields = ['id', 'note_extraite', 'ecart', 'is_suspect']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Document
        fields = [
            'id', 'dossier', 'type_doc', 'fichier',
            'taille_ko', 'mime_type', 'qualite_ocr', 'date_upload',
        ]
        read_only_fields = ['id', 'dossier', 'taille_ko', 'mime_type', 'qualite_ocr', 'date_upload']


class DossierListSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour la liste des dossiers."""
    candidat_nom = serializers.CharField(source='candidat.nom_complet', read_only=True)
    candidat_cin = serializers.CharField(source='candidat.user.cin', read_only=True)
    candidat_email = serializers.EmailField(source='candidat.user.email', read_only=True)
    filiere_nom  = serializers.CharField(source='filiere.nom', read_only=True)
    filiere_code = serializers.CharField(source='filiere.code', read_only=True)
    note_ecrite = serializers.SerializerMethodField()
    note_sur = serializers.SerializerMethodField()
    date_ecrit = serializers.SerializerMethodField()
    date_oral = serializers.SerializerMethodField()
    statut_epreuve = serializers.SerializerMethodField()
    seuil_admission = serializers.SerializerMethodField()
    lieu_oral = serializers.SerializerMethodField()
    heure_oral = serializers.SerializerMethodField()

    class Meta:
        model  = Dossier
        fields = [
            'id', 'candidat_nom', 'candidat_cin', 'candidat_email',
            'filiere_nom', 'filiere_code',
            'statut', 'score', 'classement', 'is_suspect',
            'moyenne_generale', 'date_soumission', 'created_at',
            'score_final', 'rang_final', 'note_ecrite', 'note_sur',
            'date_ecrit', 'date_oral', 'statut_epreuve', 'seuil_admission',
            'lieu_oral', 'heure_oral',
        ]

    def get_note_ecrite(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.note) if note_obj and note_obj.note is not None else None

    def get_note_sur(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.epreuve.note_sur) if note_obj else None

    def get_date_ecrit(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.date_epreuve if note_obj else None

    def get_date_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.date_oral if note_obj else None

    def get_statut_epreuve(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.statut if note_obj else None

    def get_seuil_admission(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.epreuve.seuil_admission) if note_obj else None

    def get_lieu_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.lieu_oral if note_obj else None

    def get_heure_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.heure_oral if note_obj else None


class CandidatDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_cin = serializers.CharField(source='user.cin', read_only=True)

    class Meta:
        model = Candidat
        fields = [
            'id', 'nom', 'prenom', 'telephone', 'adresse',
            'date_naissance', 'nom_complet', 'user_email', 'user_cin',
        ]
        read_only_fields = ['id', 'nom_complet', 'user_email', 'user_cin']


class DossierDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour le détail d'un dossier."""
    candidat  = CandidatDetailSerializer(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    notes     = NoteSerializer(many=True, read_only=True)
    filiere_nom  = serializers.CharField(source='filiere.nom', read_only=True)
    filiere_code = serializers.CharField(source='filiere.code', read_only=True)
    total_candidats = serializers.SerializerMethodField()
    note_ecrite = serializers.SerializerMethodField()
    note_sur = serializers.SerializerMethodField()
    date_ecrit = serializers.SerializerMethodField()
    date_oral = serializers.SerializerMethodField()
    statut_epreuve = serializers.SerializerMethodField()
    seuil_admission = serializers.SerializerMethodField()
    lieu_oral = serializers.SerializerMethodField()
    heure_oral = serializers.SerializerMethodField()

    class Meta:
        model  = Dossier
        fields = [
            'id', 'candidat', 'filiere', 'filiere_nom', 'filiere_code',
            'statut', 'diplome_obtenu', 'etablissement_origine',
            'annee_obtention', 'mention', 'moyenne_generale',
            'score', 'classement', 'motif_rejet',
            'score_confiance_ocr', 'is_suspect',
            'documents', 'notes',
            'date_soumission', 'created_at', 'updated_at', 'total_candidats',
            'score_final', 'rang_final', 'note_ecrite', 'note_sur',
            'date_ecrit', 'date_oral', 'statut_epreuve', 'seuil_admission',
            'lieu_oral', 'heure_oral',
        ]

    def get_total_candidats(self, obj):
        return Dossier.objects.filter(filiere=obj.filiere).count()

    def get_note_ecrite(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.note) if note_obj and note_obj.note is not None else None

    def get_note_sur(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.epreuve.note_sur) if note_obj else None

    def get_date_ecrit(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.date_epreuve if note_obj else None

    def get_date_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.date_oral if note_obj else None

    def get_statut_epreuve(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.statut if note_obj else None

    def get_seuil_admission(self, obj):
        note_obj = obj.notes_ecrits.first()
        return float(note_obj.epreuve.seuil_admission) if note_obj else None

    def get_lieu_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.lieu_oral if note_obj else None

    def get_heure_oral(self, obj):
        note_obj = obj.notes_ecrits.first()
        return note_obj.epreuve.heure_oral if note_obj else None


class DossierCreateUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création/modification d'un dossier."""
    notes = NoteSerializer(many=True, required=False)

    class Meta:
        model  = Dossier
        fields = [
            'id', 'filiere', 'diplome_obtenu', 'etablissement_origine',
            'annee_obtention', 'mention', 'moyenne_generale', 'notes',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        notes_data = validated_data.pop('notes', [])
        dossier = Dossier.objects.create(**validated_data)
        for note_data in notes_data:
            NoteMatiere.objects.create(dossier=dossier, **note_data)
        return dossier

    def update(self, instance, validated_data):
        notes_data = validated_data.pop('notes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if notes_data is not None:
            # Mettre à jour ou créer les notes
            for note_data in notes_data:
                NoteMatiere.objects.update_or_create(
                    dossier=instance,
                    matiere=note_data.get('matiere'),
                    defaults=note_data,
                )
        return instance
