# administration/serializers_oral.py

from rest_framework import serializers
from .models import EpreuveOrale, ConvocationOrale
from candidatures.serializers import DossierListSerializer
from users.serializers import UserSerializer

class ConvocationOraleSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source='dossier.candidat.nom', read_only=True)
    candidat_prenom = serializers.CharField(source='dossier.candidat.prenom', read_only=True)
    candidat_cin = serializers.CharField(source='dossier.candidat.user.cin', read_only=True)
    filiere_nom = serializers.CharField(source='dossier.filiere.nom', read_only=True)
    score_dossier = serializers.DecimalField(source='dossier.score', max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = ConvocationOrale
        fields = [
            'id', 'epreuve_oral', 'dossier', 'heure_passage', 'numero_passage',
            'decision', 'commentaire_jury', 'date_decision', 'decide_par',
            'bac_verifie', 'diplome_verifie', 'releve_notes_verifie', 'cin_verifie', 'dossier_complet',
            'convocation_generee', 'convocation_pdf', 'date_generation',
            'candidat_nom', 'candidat_prenom', 'candidat_cin', 'filiere_nom', 'score_dossier'
        ]
        read_only_fields = ['convocation_generee', 'convocation_pdf', 'date_generation', 'heure_passage', 'numero_passage']

class EpreuveOraleSerializer(serializers.ModelSerializer):
    filiere_nom = serializers.CharField(source='filiere.nom', read_only=True)
    filiere_code = serializers.CharField(source='filiere.code', read_only=True)
    date_oral = serializers.DateTimeField(source='filiere.date_oral', read_only=True)
    lieu_oral = serializers.CharField(source='filiere.lieu_oral', read_only=True)
    
    class Meta:
        model = EpreuveOrale
        fields = [
            'id', 'filiere', 'filiere_nom', 'filiere_code', 'epreuve_ecrite',
            'nom', 'date_oral', 'lieu_oral', 'duree_minutes',
            'statut', 'created_by', 'created_at',
            'nb_convoques', 'nb_acceptes', 'nb_refuses', 'nb_absents', 'nb_en_attente'
        ]
        read_only_fields = ['created_by']

class EpreuveOraleDetailSerializer(EpreuveOraleSerializer):
    convocations = ConvocationOraleSerializer(many=True, read_only=True)

    class Meta(EpreuveOraleSerializer.Meta):
        fields = EpreuveOraleSerializer.Meta.fields + ['convocations']
