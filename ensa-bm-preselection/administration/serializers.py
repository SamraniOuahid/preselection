# administration/serializers.py

from rest_framework import serializers
from .models import Filiere, DiplomaAccepte, HistoriqueAction


class DiplomaAccepteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DiplomaAccepte
        fields = ['id', 'nom_diplome', 'etablissements', 'is_active']


class FiliereSerializer(serializers.ModelSerializer):
    diplomes_acceptes = DiplomaAccepteSerializer(many=True, required=False)
    candidatures_count = serializers.ReadOnlyField()
    est_ouverte        = serializers.ReadOnlyField()

    class Meta:
        model  = Filiere
        fields = [
            'id', 'nom', 'code', 'niveau', 'description',
            'places_disponibles', 'is_active', 'est_ouverte',
            'date_ouverture', 'date_fermeture',
            'diplomes_acceptes', 'candidatures_count'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        diplomes_data = validated_data.pop('diplomes_acceptes', [])
        filiere = Filiere.objects.create(**validated_data)
        for d_data in diplomes_data:
            DiplomaAccepte.objects.create(filiere=filiere, **d_data)
        return filiere

    def update(self, instance, validated_data):
        diplomes_data = validated_data.pop('diplomes_acceptes', None)
        
        # Mettre à jour les champs de base de la filière
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si la liste des diplômes est fournie, on la met à jour
        if diplomes_data is not None:
            # Supprimer les anciens
            instance.diplomes_acceptes.all().delete()
            # Créer les nouveaux
            for d_data in diplomes_data:
                DiplomaAccepte.objects.create(filiere=instance, **d_data)

        return instance


class HistoriqueActionSerializer(serializers.ModelSerializer):
    acteur_nom = serializers.SerializerMethodField()

    class Meta:
        model  = HistoriqueAction
        fields = ['id', 'action', 'commentaire', 'timestamp', 'acteur_nom']

    def get_acteur_nom(self, obj):
        if obj.acteur:
            profil = getattr(obj.acteur, 'profil', None)
            return profil.nom_complet if profil else obj.acteur.email
        return "Système automatique"