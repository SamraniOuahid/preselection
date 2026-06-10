# administration/serializers_epreuve.py
# Serializers pour les épreuves écrites et notes

from rest_framework import serializers
from .models import EpreuveEcrite, NoteEcrite


class DossierInfoSerializer(serializers.Serializer):
    """Info nested du dossier dans NoteEcriteSerializer."""
    candidat_nom = serializers.CharField()
    candidat_prenom = serializers.CharField()
    candidat_cin = serializers.CharField()
    filiere_nom = serializers.CharField()
    score_dossier = serializers.DecimalField(max_digits=5, decimal_places=2)


class NoteEcriteSerializer(serializers.ModelSerializer):
    dossier_info = serializers.SerializerMethodField()

    class Meta:
        model = NoteEcrite
        fields = [
            'id', 'dossier', 'dossier_info', 'note', 'resultat',
            'rang_final', 'note_importee_le',
        ]
        read_only_fields = ['id', 'dossier_info', 'rang_final', 'note_importee_le']

    def get_dossier_info(self, obj):
        dossier = obj.dossier
        candidat = dossier.candidat
        return {
            'candidat_nom': candidat.nom,
            'candidat_prenom': candidat.prenom,
            'candidat_cin': candidat.user.cin,
            'filiere_nom': dossier.filiere.nom,
            'score_dossier': float(dossier.score or 0),
        }


class EpreuveEcriteSerializer(serializers.ModelSerializer):
    nb_admis = serializers.ReadOnlyField()
    nb_recales = serializers.ReadOnlyField()
    nb_absents = serializers.ReadOnlyField()
    moyenne_promo = serializers.ReadOnlyField()
    filiere_nom = serializers.CharField(source='filiere.nom', read_only=True)
    filiere_code = serializers.CharField(source='filiere.code', read_only=True)
    date_ecrit = serializers.DateTimeField(source='filiere.date_ecrit', read_only=True)
    lieu_ecrit = serializers.CharField(source='filiere.lieu_ecrit', read_only=True)
    date_oral = serializers.DateTimeField(source='filiere.date_oral', read_only=True)
    lieu_oral = serializers.CharField(source='filiere.lieu_oral', read_only=True)

    class Meta:
        model = EpreuveEcrite
        fields = [
            'id', 'filiere', 'filiere_nom', 'filiere_code',
            'nom', 'date_ecrit', 'lieu_ecrit', 'date_oral', 'lieu_oral', 'seuil_admission',
            'note_sur', 'coefficient', 'statut',
            'nb_admis', 'nb_recales', 'nb_absents',
            'moyenne_promo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EpreuveEcriteDetailSerializer(EpreuveEcriteSerializer):
    notes = NoteEcriteSerializer(many=True, read_only=True)

    class Meta(EpreuveEcriteSerializer.Meta):
        fields = EpreuveEcriteSerializer.Meta.fields + ['notes']


class ImportRapportSerializer(serializers.Serializer):
    """Serializer lecture seule pour la réponse d'import."""
    succes = serializers.BooleanField()
    total_lignes = serializers.IntegerField()
    importees = serializers.IntegerField()
    erreurs = serializers.ListField(child=serializers.DictField())
    non_trouves = serializers.ListField(child=serializers.DictField())
    nb_admis = serializers.IntegerField()
    nb_recales = serializers.IntegerField()
    nb_absents = serializers.IntegerField()


class NoteEcriteUpdateSerializer(serializers.ModelSerializer):
    """Pour modifier une note individuellement (correction de saisie)."""
    class Meta:
        model = NoteEcrite
        fields = ['note']
